#!/usr/bin/env python3
"""Ejecuta crawlers aislados y los reinicia si Chrome o Python mueren.

Cada worker recibe un shard determinista de dominios. Los JSON ya guardados actuan
como checkpoint, asi que un reinicio solo vuelve a intentar lo que quedo incompleto.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time


@dataclass
class WorkerState:
    index: int
    process: subprocess.Popen | None = None
    stdout_handle: object | None = None
    stderr_handle: object | None = None
    restarts: int = 0
    next_start: float = 0.0
    complete: bool = False
    failed: bool = False


def build_worker_command(args, worker_index):
    crawler = Path(__file__).with_name("crawl.py")
    command = [
        args.python, "-u", str(crawler),
        "--input", str(Path(args.input).resolve()),
        "--out", str(Path(args.out).resolve()),
        "--max-pages", str(args.max_pages),
        "--depth", str(args.depth),
        "--concurrency", str(args.concurrency_per_worker),
        "--http-concurrency", str(args.http_concurrency_per_worker),
        "--domain-timeout", str(args.domain_timeout),
        "--max-attempts", str(args.max_attempts),
        "--shard-count", str(args.workers),
        "--shard-index", str(worker_index),
        "--cycle-size", str(args.cycle_size),
    ]
    if args.supabase:
        command.extend(["--supabase", "--skip-ensure-table"])
    return command


def close_logs(state):
    for handle_name in ("stdout_handle", "stderr_handle"):
        handle = getattr(state, handle_name)
        if handle:
            handle.close()
            setattr(state, handle_name, None)


def start_worker(state, args, log_dir):
    stdout_path = log_dir / f"worker-{state.index + 1}.out.log"
    stderr_path = log_dir / f"worker-{state.index + 1}.err.log"
    state.stdout_handle = stdout_path.open("a", encoding="utf-8", buffering=1)
    state.stderr_handle = stderr_path.open("a", encoding="utf-8", buffering=1)
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    state.process = subprocess.Popen(
        build_worker_command(args, state.index),
        cwd=str(Path.cwd()),
        stdout=state.stdout_handle,
        stderr=state.stderr_handle,
        creationflags=creationflags,
    )
    print(
        f"worker {state.index + 1}/{args.workers} iniciado "
        f"pid={state.process.pid} intento={state.restarts + 1}",
        flush=True,
    )


def stop_workers(states):
    for state in states:
        process = state.process
        if process and process.poll() is None:
            process.terminate()
    deadline = time.time() + 10
    for state in states:
        process = state.process
        if not process:
            continue
        remaining = max(0.0, deadline - time.time())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            process.kill()
        close_logs(state)


def supervise(args):
    if args.workers < 1:
        raise ValueError("--workers debe ser >= 1")
    if args.concurrency_per_worker < 1:
        raise ValueError("--concurrency-per-worker debe ser >= 1")
    if args.http_concurrency_per_worker < 1:
        raise ValueError("--http-concurrency-per-worker debe ser >= 1")
    if args.cycle_size < 1:
        raise ValueError("--cycle-size debe ser >= 1")
    if args.max_attempts < 1:
        raise ValueError("--max-attempts debe ser >= 1")

    if args.supabase:
        import load_supabase as sink
        # La llave vigente sólo vive en el entorno de este supervisor y sus hijos.
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = sink.SERVICE_KEY
        sink.ensure_table()

    log_dir = Path(args.log_dir or f"{args.out}_supervisor_logs").resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    Path(args.out).resolve().mkdir(parents=True, exist_ok=True)
    states = [WorkerState(index=index) for index in range(args.workers)]
    print(
        f"Supervisor: {args.workers} workers x {args.concurrency_per_worker} pestañas Chrome "
        f"+ {args.http_concurrency_per_worker} HTTP por worker. Logs: {log_dir}",
        flush=True,
    )

    try:
        while True:
            now = time.time()
            for state in states:
                if state.complete or state.failed:
                    continue
                if state.process is None:
                    if now >= state.next_start:
                        start_worker(state, args, log_dir)
                    continue

                exit_code = state.process.poll()
                if exit_code is None:
                    continue
                close_logs(state)
                state.process = None
                if exit_code == 0:
                    state.complete = True
                    print(f"worker {state.index + 1} completo", flush=True)
                    continue
                if exit_code == 80:
                    state.next_start = time.time() + 1
                    print(
                        f"worker {state.index + 1} completo su lote; "
                        "Chrome nuevo en 1s",
                        flush=True,
                    )
                    continue

                state.restarts += 1
                if exit_code == 2 or (
                    args.max_restarts > 0 and state.restarts > args.max_restarts
                ):
                    state.failed = True
                    print(
                        f"worker {state.index + 1} detenido: exit={exit_code}, "
                        f"restarts={state.restarts}",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue

                backoff = min(60, 3 * (2 ** min(state.restarts - 1, 5)))
                state.next_start = time.time() + backoff
                print(
                    f"worker {state.index + 1} cayo (exit={exit_code}); "
                    f"reinicio automatico en {backoff}s",
                    file=sys.stderr,
                    flush=True,
                )

            if any(state.failed for state in states):
                return 1
            if all(state.complete for state in states):
                return 0
            time.sleep(1)
    except KeyboardInterrupt:
        print("Supervisor interrumpido; cerrando workers...", file=sys.stderr, flush=True)
        return 130
    finally:
        stop_workers(states)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--concurrency-per-worker", type=int, default=3)
    parser.add_argument("--http-concurrency-per-worker", type=int, default=12)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--domain-timeout", type=int, default=45)
    parser.add_argument("--cycle-size", type=int, default=100,
                        help="dominios por proceso antes de reciclar Chrome (def 100).")
    parser.add_argument("--max-attempts", type=int, default=2,
                        help="intentos totales por dominio fallido (def 2).")
    parser.add_argument("--max-restarts", type=int, default=20,
                        help="reinicios por worker; 0 significa ilimitados (def 20).")
    parser.add_argument("--log-dir")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--supabase", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return supervise(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

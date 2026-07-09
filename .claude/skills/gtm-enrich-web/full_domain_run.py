import json, concurrent.futures, threading, time
from parallel import Parallel

sp = '/tmp/claude-0/-home-user-unprospect-gtm/b4f6a0e7-3f0c-5545-8b2f-e4c03620cf05/scratchpad'
rows = json.load(open(f'{sp}/full_run_input.json'))
outfile = f'{sp}/full_domain_results.jsonl'
done_ids = set()
try:
    for line in open(outfile):
        done_ids.add(json.loads(line)["id"])
except FileNotFoundError:
    pass
todo = [r for r in rows if r["id"] not in done_ids]
print(f"total {len(rows)} | ya hechos {len(done_ids)} | por hacer {len(todo)}", flush=True)

client = Parallel()
lock = threading.Lock()

schema = {
  "type": "json",
  "json_schema": {
    "type": "object",
    "properties": {
      "domain": {"type": ["string","null"], "description": "Official website domain of this exact legal entity, host only (no https://, no www, no path). Must be the company's OWN site - never directories, aggregators, marketplaces, news sites, or CONDUSEF/government pages. If the SOFOM operates inside a parent group's website, return the group's domain. null if no official site can be confirmed or the company is defunct."},
      "company_alive": {"type": "boolean", "description": "false if the company appears defunct, in liquidation, revoked, or its web presence is dead."},
      "evidence": {"type": "string", "description": "One short sentence: how the domain was confirmed (which page/legal text), or why null."}
    },
    "required": ["domain","company_alive","evidence"],
    "additionalProperties": False
  }
}

def run_one(p):
    inp = (f"Mexican SOFOM (non-bank lender) registered in SIPRES/CONDUSEF.\n"
           f"Legal name (razon social): {p['razon_social']}\n"
           f"Brand name (nombre comercial): {p['nombre_comercial']}\n"
           f"State: {p['estado']}, Mexico.\n"
           f"Find its official website domain. Verify the site belongs to THIS exact legal entity "
           f"(razon social in footer/aviso de privacidad/legal text). Similar names are NOT a match. "
           f"Directories (CONDUSEF, dun&bradstreet, empresite, etc.) are NOT the company's site. "
           f"A wrong answer is worse than null.")
    for attempt in range(3):
        try:
            tr = client.task_run.create(input=inp, processor="lite", task_spec={"output_schema": schema},
                                        metadata={"codigo": p["codigo"]})
            res = client.task_run.result(tr.run_id, api_timeout=1800)
            out = res.output.content if hasattr(res.output, "content") else res.output
            if isinstance(out, str): out = json.loads(out)
            rec = {"id": p["id"], "codigo": p["codigo"], "razon_social": p["razon_social"],
                   "nombre_comercial": p["nombre_comercial"], **out}
            break
        except Exception as e:
            if attempt == 2:
                rec = {"id": p["id"], "codigo": p["codigo"], "razon_social": p["razon_social"],
                       "nombre_comercial": p["nombre_comercial"], "error": str(e)[:250]}
            else:
                time.sleep(5 * (attempt + 1))
    with lock:
        with open(outfile, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

start = time.time()
count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for _ in ex.map(run_one, todo):
        count += 1
        if count % 50 == 0:
            rate = count / (time.time() - start)
            print(f"{count}/{len(todo)} | {rate*60:.0f}/min | ETA {((len(todo)-count)/rate)/60:.0f} min", flush=True)
print("RUN COMPLETE:", count, flush=True)

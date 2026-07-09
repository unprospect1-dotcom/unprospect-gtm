"""Config compartida para correr Chromium/Playwright dentro del sandbox CCR.

Resuelve tres cosas que rompen cualquier scraper con JS aquí:
  1. Playwright empaquetado pide un build de chromium que no está -> usar el binario
     preinstalado en /opt/pw-browsers/chromium via executable_path.
  2. Todo el egress pasa por el proxy local del sandbox (--proxy-server) y hay que
     no-bypassear loopback (--proxy-bypass-list=<-loopback>).
  3. El middlebox de inspección TLS resetea el ClientHello grande de TLS1.3
     (post-quantum keyshare) -> forzar --ssl-version-max=tls1.2.
El CA de MITM ya debe estar importado en ~/.pki/nssdb (ver bootstrap_nss()).
"""
import os, subprocess

CHROMIUM = "/opt/pw-browsers/chromium"
PROXY = os.environ.get("HTTPS_PROXY", "http://127.0.0.1:33803")

LAUNCH_ARGS = [
    "--no-sandbox",
    f"--proxy-server={PROXY}",
    "--proxy-bypass-list=<-loopback>",
    "--ssl-version-max=tls1.2",
    "--disable-dev-shm-usage",
]

def bootstrap_nss():
    """Importa el CA bundle del proxy en el NSS store de Chromium (idempotente).

    OJO: nunca correr `certutil -N` sobre un db existente -> pide password y cuelga.
    Solo inicializa el db si no existe; el import de CA es idempotente.
    """
    db = os.path.expanduser("~/.pki/nssdb")
    os.makedirs(db, exist_ok=True)
    if not os.path.exists(os.path.join(db, "cert9.db")):
        subprocess.run(["certutil", "-d", f"sql:{db}", "-N", "--empty-password"],
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=20)
    # ya presente?
    listing = subprocess.run(["certutil", "-d", f"sql:{db}", "-L"],
                             capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=20)
    if "ccr-proxy-ca" not in listing.stdout:
        subprocess.run(["certutil", "-d", f"sql:{db}", "-A", "-t", "C,,",
                        "-n", "ccr-proxy-ca", "-i", "/root/.ccr/ca-bundle.crt"],
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=20)

def launch_kwargs():
    return dict(headless=True, executable_path=CHROMIUM, args=LAUNCH_ARGS)

def patch_crawl4ai():
    """Inyecta executable_path en el launch de crawl4ai (no lo expone su API)."""
    from crawl4ai import browser_manager as bm
    orig = bm.BrowserManager._build_browser_args
    def patched(self):
        d = orig(self)
        d["executable_path"] = CHROMIUM
        d.setdefault("args", [])
        for a in ("--ssl-version-max=tls1.2", "--proxy-bypass-list=<-loopback>", "--no-sandbox"):
            if a not in d["args"]:
                d["args"].append(a)
        return d
    bm.BrowserManager._build_browser_args = patched

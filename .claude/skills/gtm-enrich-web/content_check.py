import json, re, subprocess, unicodedata, concurrent.futures
sp = '/tmp/claude-0/-home-user-unprospect-gtm/b4f6a0e7-3f0c-5545-8b2f-e4c03620cf05/scratchpad'
recs = [json.loads(l) for l in open(f'{sp}/full_domain_results.jsonl')]
found = [r for r in recs if r.get("domain")]

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()
def tokens(s):
    stop = {"de","del","la","el","los","las","y","en","sa","sapi","cv","sofom","enr","er","sc","rl","sofome"}
    return [t for t in norm(s).split() if len(t) > 3 and t not in stop]

def check(r):
    d = r["domain"].lower().removeprefix("www.")
    try:
        p = subprocess.run(["curl","-sL","--compressed","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "--max-time","20","--max-filesize","2000000",f"https://www.{d}"],
                           capture_output=True, timeout=25)
        html = norm(p.stdout.decode("utf-8","ignore"))
        if len(html) < 200:
            p = subprocess.run(["curl","-sL","--compressed","-A","Mozilla/5.0","--max-time","15",f"https://{d}"],
                               capture_output=True, timeout=20)
            html = norm(p.stdout.decode("utf-8","ignore"))
        if len(html) < 200:
            return r["id"], "unreachable"
        toks = set(tokens(r["razon_social"]) + tokens(r["nombre_comercial"]))
        hits = sum(1 for t in toks if t in html)
        rs_full = norm(re.sub(r",?\s*S\.?A\.?(P\.?I\.?)?\s*DE\s*C\.?V\.?.*$", "", r["razon_social"], flags=re.I))
        if rs_full and rs_full in html: return r["id"], "confirmed_legal"
        if hits >= 2 or (len(toks) == 1 and hits == 1): return r["id"], "confirmed_tokens"
        if hits == 1: return r["id"], "weak"
        return r["id"], "no_match"
    except Exception:
        return r["id"], "unreachable"

out = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
    for id_, v in ex.map(check, found):
        out[id_] = v
json.dump(out, open(f'{sp}/content_check.json','w'))
from collections import Counter
print(Counter(out.values()))

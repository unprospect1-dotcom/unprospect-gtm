import json, concurrent.futures
from parallel import Parallel

sp = '/tmp/claude-0/-home-user-unprospect-gtm/b4f6a0e7-3f0c-5545-8b2f-e4c03620cf05/scratchpad'
pilot = json.load(open(f'{sp}/pilot20.json'))
client = Parallel()

schema = {
  "type": "json",
  "json_schema": {
    "type": "object",
    "properties": {
      "domain": {"type": ["string","null"], "description": "Official website domain of this exact legal entity, host only (no https://, no www, no path). If the SOFOM lives inside its financial group's website, return the group's domain. null if no official site can be confirmed or the company is defunct."},
      "linkedin_url": {"type": ["string","null"], "description": "Official LinkedIn COMPANY page URL (linkedin.com/company/<slug>). Must be the claimed/real page of this entity or its operating brand - never personal profiles, never unclaimed auto-generated stubs. null if none exists."},
      "company_alive": {"type": "boolean", "description": "false if the company appears defunct, in liquidation, or its web presence is dead."},
      "evidence": {"type": "string", "description": "One sentence: how each field was confirmed (which page/legal text)."}
    },
    "required": ["domain","linkedin_url","company_alive","evidence"],
    "additionalProperties": False
  }
}

def run_one(p):
    inp = (f"Mexican SOFOM (non-bank lender) registered in SIPRES/CONDUSEF.\n"
           f"Legal name (razon social): {p['razon_social']}\n"
           f"Brand name (nombre comercial): {p['nombre_comercial']}\n"
           f"State: {p['estado']}, Mexico.\n"
           f"Find its official website domain and official LinkedIn company page. "
           f"Verify the site belongs to THIS exact legal entity (razon social in footer/aviso de privacidad). "
           f"Similar names are NOT a match. A wrong answer is worse than null.")
    tr = client.task_run.create(input=inp, processor="lite", task_spec={"output_schema": schema},
                                metadata={"codigo": p["codigo"]})
    res = client.task_run.result(tr.run_id, api_timeout=1800)
    return {"id": p["id"], "codigo": p["codigo"], "run_id": tr.run_id,
            "output": res.output.content if hasattr(res.output, "content") else res.output}

out = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(run_one, p): p for p in pilot}
    for f in concurrent.futures.as_completed(futs):
        p = futs[f]
        try:
            r = f.result(); out.append(r); print("OK", p["codigo"], json.dumps(r["output"], ensure_ascii=False)[:160])
        except Exception as e:
            out.append({"id": p["id"], "codigo": p["codigo"], "error": str(e)[:300]}); print("ERR", p["codigo"], str(e)[:200])

json.dump(out, open(f'{sp}/parallel_results.json','w'), ensure_ascii=False, indent=1)
print("done:", len(out))

import os, json, urllib.request
from collections import Counter

base = os.environ['SUPABASE_URL'] + '/rest/v1'
token = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {'apikey': token, 'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}

def fetch(offset):
    url = f"{base}/companies?select=id,name,domain,parallel_cat,vertical_broad,industry,origin&limit=1000&offset={offset}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

rows = []
offset = 0
while True:
    page = fetch(offset)
    if not page:
        break
    rows.extend(page)
    if len(page) < 1000:
        break
    offset += 1000

print('TOTAL_ROWS', len(rows))

def is_transport(r):
    vb = (r.get('vertical_broad') or '').lower()
    ind = (r.get('industry') or '').lower()
    pc = (r.get('parallel_cat') or {})
    pv = str(pc.get('vertical') or '').lower()
    cat = str(pc.get('categoria') or '').lower()
    text = ' '.join([vb, ind, pv, cat])
    keywords = ['transport', 'transporte', 'logistic', 'logistics', 'freight', 'cargo', 'truck', 'shipping', '3pl', 'warehouse', 'distribution', 'supply chain', 'supply', 'courier', 'maritime']
    return any(k in text for k in keywords)

transport = [r for r in rows if is_transport(r)]
print('TRANSPORT_MATCHES', len(transport))
print('SAMPLE')
for r in transport[:20]:
    print(r.get('name'), '|', r.get('vertical_broad'), '|', r.get('industry'))

# Also count explicit vertical broad buckets for transport-ish rows
counts = Counter((r.get('vertical_broad') or '').strip() for r in transport if (r.get('vertical_broad') or '').strip())
print('VERTICAL_BROAD_COUNTS')
for k,v in counts.most_common():
    print(k, v)

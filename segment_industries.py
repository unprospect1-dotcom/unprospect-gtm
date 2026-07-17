import os, json, urllib.request
from collections import Counter

base = os.environ['SUPABASE_URL'] + '/rest/v1'
token = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {'apikey': token, 'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}

def fetch(offset):
    url = f"{base}/companies?select=id,name,domain,parallel_cat,vertical_broad,industry,subniche,niche,description_short,origin&limit=1000&offset={offset}"
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

def bucket(r):
    vb = (r.get('vertical_broad') or '').strip()
    if vb:
        return vb
    text = ' '.join([
        str(r.get('industry') or ''),
        str(r.get('subniche') or ''),
        str(r.get('niche') or ''),
        str(r.get('description_short') or ''),
        str((r.get('parallel_cat') or {}).get('vertical') or ''),
        str((r.get('parallel_cat') or {}).get('categoria') or '')
    ]).lower()
    if any(k in text for k in ['software','ti','technology','saas','ai','data','cloud','cyber','devops','digital']):
        return 'Software/TI'
    if any(k in text for k in ['manufactur','industrial','fabric','metal','machine','machinery','factory','production','equipment','ingenier']):
        return 'Manufactura/Industrial'
    if any(k in text for k in ['transport','transporte','logistic','logistics','3pl','freight','shipping','cargo','warehouse','distribution','supply','courier']):
        return 'Logística y Transporte'
    if any(k in text for k in ['health','medical','pharma','biotech','hospital','clin']):
        return 'Salud y Farma'
    if any(k in text for k in ['retail','consumo','ecommerce','commerce']):
        return 'Retail/Consumo'
    if any(k in text for k in ['financ','bank','insurance','seguros','accounting','payment']):
        return 'Finanzas/Seguros'
    if any(k in text for k in ['constru','real estate','inmobili','building','construction']):
        return 'Construcción/Inmobiliario'
    if any(k in text for k in ['educat','school','university','elearning']):
        return 'Educación'
    if any(k in text for k in ['energy','oil','gas','utilities','renewable']):
        return 'Energía'
    if any(k in text for k in ['food','beverage','restaurant','aliment']):
        return 'Alimentos y Bebidas'
    if any(k in text for k in ['recruit','rrhh','talent','human resources','staffing','headhunting']):
        return 'RRHH/Talento'
    if any(k in text for k in ['telecom','media','advertis','marketing','communication','public relations']):
        return 'Telecom/Medios'
    if any(k in text for k in ['gov','government','ngo','nonprofit']):
        return 'Gobierno/ONG'
    if any(k in text for k in ['chemic','quimic']):
        return 'Química'
    if any(k in text for k in ['consult','service','professional','advisory','outsourcing']):
        return 'Servicios profesionales'
    return 'Otros'

counts = Counter(bucket(r) for r in rows)
for k, v in counts.most_common():
    print(f'{k}={v}')

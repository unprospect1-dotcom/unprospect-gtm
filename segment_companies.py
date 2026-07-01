import os
import csv
import json
import urllib.request
from collections import Counter


def normalize_text(value):
    return ' '.join(str(value or '').lower().split())


def parse_parallel_cat(row):
    parallel_cat = row.get('parallel_cat') or {}
    if isinstance(parallel_cat, str):
        try:
            parallel_cat = json.loads(parallel_cat) if parallel_cat else {}
        except json.JSONDecodeError:
            parallel_cat = {}
    return parallel_cat if isinstance(parallel_cat, dict) else {}


def classify_company(row):
    name = normalize_text(row.get('name') or '')
    industry = normalize_text(row.get('industry') or '')
    parallel_cat = parse_parallel_cat(row)
    parallel_vertical = normalize_text(parallel_cat.get('vertical') or '')
    parallel_categoria = normalize_text(parallel_cat.get('categoria') or '')

    text = ' '.join([name, industry, parallel_vertical, parallel_categoria])

    if any(k in text for k in ['3pl', 'third party logistics', 'warehouse', 'warehousing', 'fulfillment', 'distribution center', 'storage']):
        if any(k in text for k in ['truck', 'trucking', 'carrier', 'freight', 'transport', 'shipping', 'courier', 'last mile', 'delivery', 'cargo']):
            return '3pl_warehousing', '3PL/warehouse with transport signal'
        return '3pl_warehousing', '3PL/warehouse or storage'

    if any(k in text for k in ['freight forward', 'forwarding', 'ocean freight', 'air freight', 'broker']):
        return 'freight_forwarding', 'Freight forwarding or broker'

    if any(k in text for k in ['truck', 'trucking', 'carrier', 'transport', 'transportation', 'courier', 'last mile', 'delivery', 'cargo']):
        return 'transport_terrestre', 'Ground transport / trucking / delivery'

    if any(k in text for k in ['maritime', 'shipping', 'port', 'sea freight', 'ocean']):
        return 'maritime_shipping', 'Maritime / shipping'

    if any(k in text for k in ['supply chain', 'logistics', 'logistic']):
        return 'review', 'Review: ambiguous logistics broad label'

    return 'review', 'No strong subsegment signal'


def fetch_rows(limit=1000, offset=0):
    base = os.environ['SUPABASE_URL'] + '/rest/v1'
    token = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': token, 'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    url = f"{base}/companies?select=id,name,domain,parallel_cat,vertical_broad,industry&limit={limit}&offset={offset}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def build_segments():
    rows = []
    offset = 0
    while True:
        page = fetch_rows(offset=offset)
        if not page:
            break
        rows.extend(page)
        if len(page) < 1000:
            break
        offset += 1000

    buckets = Counter()
    reasons = Counter()
    classified = []
    for row in rows:
        bucket, reason = classify_company(row)
        buckets[bucket] += 1
        reasons[reason] += 1
        classified.append({
            'id': row.get('id'),
            'name': row.get('name'),
            'domain': row.get('domain'),
            'vertical_broad': row.get('vertical_broad'),
            'industry': row.get('industry'),
            'parallel_cat': row.get('parallel_cat'),
            'bucket': bucket,
            'reason': reason,
        })

    with open('segment_results.json', 'w', encoding='utf-8') as fh:
        json.dump({'total_rows': len(rows), 'buckets': dict(buckets), 'reasons': dict(reasons), 'classified': classified}, fh, ensure_ascii=False, indent=2)

    with open('segment_results.csv', 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['id', 'name', 'domain', 'vertical_broad', 'industry', 'bucket', 'reason'])
        writer.writeheader()
        for item in classified:
            row = {k: item.get(k) for k in ['id', 'name', 'domain', 'vertical_broad', 'industry', 'bucket', 'reason']}
            writer.writerow(row)

    return rows, buckets, reasons


if __name__ == '__main__':
    rows, buckets, reasons = build_segments()
    print('TOTAL_ROWS', len(rows))
    print('BUCKET_COUNTS')
    for k, v in buckets.most_common():
        print(k, v)
    print('REASONS')
    for k, v in reasons.most_common(20):
        print(k, v)
    print('OUTPUT', 'segment_results.json')

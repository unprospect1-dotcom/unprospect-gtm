import json
import os
import urllib.request
from typing import List, Dict, Tuple


class SpecialistAgent:
    def __init__(self, name: str, bucket: str, keywords: List[str], confidence: float = 0.85):
        self.name = name
        self.bucket = bucket
        self.keywords = [k.lower() for k in keywords]
        self.confidence = confidence

    def score(self, row: Dict) -> Tuple[bool, str]:
        text = ' '.join([
            str(row.get('name') or ''),
            str(row.get('industry') or ''),
            str(row.get('vertical_broad') or ''),
            str((row.get('parallel_cat') or {}).get('vertical') or ''),
            str((row.get('parallel_cat') or {}).get('categoria') or ''),
        ]).lower()
        matched = [k for k in self.keywords if k in text]
        if matched:
            return True, ', '.join(matched[:3])
        return False, ''


class ManagerOrchestrator:
    def __init__(self):
        self.specialists = [
            SpecialistAgent('transport', 'transport_terrestre', ['truck', 'trucking', 'carrier', 'transport', 'delivery', 'cargo']),
            SpecialistAgent('3pl', '3pl_warehousing', ['3pl', 'warehouse', 'warehousing', 'fulfillment', 'storage']),
            SpecialistAgent('freight', 'freight_forwarding', ['freight forward', 'forwarding', 'broker', 'ocean freight', 'air freight']),
            SpecialistAgent('maritime', 'maritime_shipping', ['maritime', 'shipping', 'port', 'ocean freight']),
        ]

    def classify_row(self, row: Dict) -> Dict:
        results = []
        for specialist in self.specialists:
            matched, evidence = specialist.score(row)
            if matched:
                results.append({
                    'agent': specialist.name,
                    'bucket': specialist.bucket,
                    'confidence': specialist.confidence,
                    'evidence': evidence,
                })

        if not results:
            return {
                'bucket': 'review',
                'confidence': 0.2,
                'agent': 'manager',
                'reason': 'No specialist matched strongly',
            }

        best = max(results, key=lambda x: x['confidence'])
        return {
            'bucket': best['bucket'],
            'confidence': best['confidence'],
            'agent': best['agent'],
            'reason': best['evidence'],
        }

    def classify_rows(self, rows: List[Dict]) -> List[Dict]:
        output = []
        for row in rows:
            result = self.classify_row(row)
            output.append({
                'id': row.get('id'),
                'name': row.get('name'),
                'domain': row.get('domain'),
                'vertical_broad': row.get('vertical_broad'),
                'industry': row.get('industry'),
                'bucket': result['bucket'],
                'confidence': result['confidence'],
                'agent': result['agent'],
                'reason': result['reason'],
            })
        return output


def fetch_rows(limit=1000, offset=0):
    base = os.environ['SUPABASE_URL'] + '/rest/v1'
    token = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': token, 'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
    url = f"{base}/companies?select=id,name,domain,parallel_cat,vertical_broad,industry&limit={limit}&offset={offset}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main():
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

    orchestrator = ManagerOrchestrator()
    classified = orchestrator.classify_rows(rows)
    with open('subagent_results.json', 'w', encoding='utf-8') as fh:
        json.dump(classified, fh, ensure_ascii=False, indent=2)
    print('WROTE', len(classified), 'rows to subagent_results.json')


if __name__ == '__main__':
    main()

"""Prepare a clearly artificial UI fixture; never submit an API action."""
import csv
from decimal import Decimal
from http.client import HTTPConnection
import io
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.execution_comparison import mapping_template, POLICY

out = root / 'reports/phase6-execution-comparison-2026-10-22'
out.mkdir(exist_ok=True)
fixtures = root / '.local/ev-data'
run = '72061a4aa7a0455cb400edcc580cb964'
session = '0190241d62b543c6b69b4a5db31051d6'
reference = json.loads((root / '.local/dukascopy-research' / run / 'simulation.json').read_bytes())
metadata = {'producer': 'Ejemplo artificial de QA; derivado de Python, no de otro simulador', 'origin': 'synthetic_fixture',
    **{key: reference['configuration'][key] for key in ('pair','currency','strategy','fast','slow')},
    'start_date': reference['source']['start_date'], 'end_date_exclusive': reference['source']['end_date_exclusive'],
    'sessions_sha256': reference['sessions_sha256']}
settings = {**POLICY, 'alignment_window_seconds': 60}
stream = io.StringIO(newline='')
writer = csv.DictWriter(stream, fieldnames=list(mapping_template()['columns']))
writer.writeheader()
for i, fill in enumerate(reference['hypothetical_fills']):
    row = {'external_id': f'SYNTHETIC-QA-{i+1}', 'side': fill['side'], 'executed_at': fill['executed_at'],
        'signal_at': fill['signal_at'], 'quantity': fill['quantity'], 'price': fill['price'], 'fee': fill['assumed_commission']}
    if i == 0: row['price'] = str(Decimal(row['price']) + Decimal('0.0001'))
    if i == 1: row['executed_at'] = '2025-10-15T00:01:00.000Z'
    if i == 2: row['fee'] = ''
    writer.writerow(row)
(fixtures / 'execution-comparison-fixture.csv').write_bytes(stream.getvalue().encode('utf-8'))
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for name, value in [('execution-mapping.json', mapping_template()), ('execution-metadata.json', metadata), ('execution-tolerances.json', settings)]:
    save(fixtures / name, value)
def get(path):
    conn = HTTPConnection('127.0.0.1',64162,timeout=10)
    try:
        conn.request('GET',path); response=conn.getresponse(); assert response.status==200
        return json.loads(response.read())
    finally: conn.close()
chat = get('/api/chat/'+session)
assert not any(job['state'] in ('queued','running') for job in chat['jobs'])
manual = get('/api/chat/'+session+'/manual-operations')
strategy = get('/api/simulation')
baseline = {'reserved': chat['reserved'], 'manual_accounts': {a['id']: {'state': a['state'], 'chain_sha256': a['chain_sha256']} for a in manual['accounts']},
    'strategy_accounts': strategy['accounts'], 'strategy_receipts': strategy['receipts']}
save(fixtures/'execution-before.json', baseline)
protocol = {'date':'2026-10-22', 'reference_run':run, 'reference_sha256':reference['result_sha256'], 'session':session,
    'published_base_commit':'0bd90113c5ea47731da52a57d26d9b5f6dfeafdc', 'fixture_origin':'synthetic_fixture',
    'fixture_method':'Reexport existing Python fills and deliberately alter price, time and a missing fee; not an external report.',
    'changes': [{'reference_index':1,'field':'price','delta':'0.0001'}, {'reference_index':2,'field':'executed_at','delta_seconds':60},
        {'reference_index':3,'field':'fee','external_value':None}],
    'mapping':mapping_template(), 'metadata':metadata, 'tolerances':settings,
    'expected':{'status':'differences','pairs':3,'rows_with_differences':2,'unknown_fields':['fee'],'missing':0,'extra':0},
    'own_model_requests':0,'new_backtests':0,'account_operations':0,'real_external_equivalence_pending':True,
    'phase_closed':False,'commit_and_push_authorized_this_increment':False}
assert not (out/'protocol.json').exists()
save(out/'protocol.json', protocol)
print(json.dumps({'fixture_ready':True, 'active_jobs':False, 'reserved_observed':baseline['reserved'], 'manual_accounts':len(baseline['manual_accounts'])}))

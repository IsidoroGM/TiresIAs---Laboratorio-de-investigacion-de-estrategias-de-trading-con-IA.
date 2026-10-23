"""Independent, read-only audit; do not import the project comparator or engine."""
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from http.client import HTTPConnection
import io
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[2]
out=root/'reports/phase6-execution-comparison-2026-10-22'
identity='7bc438f1cfe23bc13f0589e2b18ce0335771bfe790cf217c982a1c3d41306e79'
archive=root/'.local/execution-comparisons'/identity
def digest(path):return sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def checksum(value):return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
def put(relative,raw):
    path=out/relative;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,relative
    else:
        with path.open('xb') as stream:stream.write(raw)
def save(relative,value):put(relative,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def get(path):
    connection=HTTPConnection('127.0.0.1',64162,timeout=10)
    try:
        connection.request('GET',path);response=connection.getresponse();assert response.status==200
        return json.loads(response.read())
    finally:connection.close()

prior={}
for path in sorted((root/'reports').rglob('manifest.json')):
    if path.is_relative_to(out):continue
    entries=read(path).get('evidence_sha256')
    if not isinstance(entries,dict):continue
    for relative,expected in entries.items():
        target=(path.parent/relative).resolve();assert target.is_relative_to(root)
        assert digest(target)==expected,(path,relative)
    prior[path.relative_to(root).as_posix()]={'sha256':digest(path),'files_verified':len(entries)}
assert len(prior)==12,len(prior)
previous=read(root/'reports/phase6-manual-valuation-2026-10-22/manifest.json')
unchanged={key:value for key,value in (previous['unchanged_prior_source_sha256']|previous['source_sha256']).items()
    if key not in ('trading_ai/tv_service.py','trading_ai/lab_static/simulation.js')}
for path,expected in unchanged.items():assert digest(root/path)==expected,path
prices=read(root/'reports/phase6-chat-operations-2026-10-22/manifest.json')['original_price_sha256']
for name,expected in prices.items():assert digest(Path('C:/Users/34656/Downloads')/name)==expected
assert digest(root/'docs/PROJECT_STATUS.md')=='9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb'
protocol=read(out/'protocol.json')
for ref in ('HEAD','origin/main'):
    assert subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip()==protocol['published_base_commit']
stored=read(archive/'comparison.json');reference=read(archive/'reference-simulation.json')
assert stored==get('/api/simulation/execution-comparisons/'+identity)
assert checksum(stored)==identity and checksum({key:value for key,value in reference.items() if key!='result_sha256'})==protocol['reference_sha256']
assert stored['reference_sha256']==reference['result_sha256']==protocol['reference_sha256']
assert stored['declaration']==protocol['metadata'] and stored['policy']==protocol['tolerances']
assert stored['declaration']['origin']=='synthetic_fixture'
assert not any(stored[key] for key in ('external_origin_verified','external_format_verified','external_equivalence_verified','accounting_processed','external_orders_sent'))
manifest=read(archive/'manifest.json')
for name,expected in manifest['evidence_sha256'].items():
    assert digest(archive/name)==expected,name
    put('results/'+name,(archive/name).read_bytes())
put('results/manifest.json',(archive/'manifest.json').read_bytes())
assert (archive/'original.csv').read_bytes()==(root/'.local/ev-data/execution-comparison-fixture.csv').read_bytes()
rows=list(csv.DictReader(io.StringIO((archive/'original.csv').read_text(encoding='utf-8'),newline='')))
fills=reference['hypothetical_fills'];assert len(rows)==len(fills)==3
independent=[]
for i,(row,fill) in enumerate(zip(rows,fills)):
    assert row['side']==fill['side'] and Decimal(row['quantity'])==Decimal(fill['quantity']) and row['signal_at']==fill['signal_at']
    price=Decimal(row['price'])-Decimal(fill['price'])
    seconds=(datetime.fromisoformat(row['executed_at'].replace('Z','+00:00'))-datetime.fromisoformat(fill['executed_at'].replace('Z','+00:00'))).total_seconds()
    fee=None if not row['fee'] else Decimal(row['fee'])-Decimal(fill['assumed_commission'])
    assert price==(Decimal('0.0001') if i==0 else Decimal('0'))
    assert seconds==(60 if i==1 else 0)
    assert fee==(None if i==2 else Decimal('0'))
    independent.append({'reference_index':i+1,'price_delta':str(price),'time_delta_seconds':seconds,'fee_delta':None if fee is None else str(fee)})
comparison=stored['comparison']
assert comparison['status']=='differences' and len(comparison['pairs'])==3
assert not comparison['missing'] and not comparison['extra'] and not comparison['ambiguous'] and not comparison['errors']
assert [p['reference']['index'] for p in comparison['pairs']]==[1,2,3]
assert [p['external']['line'] for p in comparison['pairs']]==[2,3,4]
assert [[d['field'] for d in p['differences']] for p in comparison['pairs']]==[['price'],['executed_at'],[]]
assert comparison['unknown_fields']==['fee'] and comparison['pairs'][2]['external']['fee'] is None
assert Decimal(comparison['pairs'][0]['differences'][0]['external_minus_python'])==Decimal('0.0001')
assert comparison['pairs'][1]['differences'][0]['external_minus_python_seconds']==60
baseline=read(root/'.local/ev-data/execution-before.json')
manual=get('/api/chat/'+protocol['session']+'/manual-operations')
current_accounts={a['id']:{'state':a['state'],'chain_sha256':a['chain_sha256']} for a in manual['accounts']}
assert current_accounts==baseline['manual_accounts']
strategy=get('/api/simulation')
assert strategy['accounts']==baseline['strategy_accounts']==[] and strategy['receipts']==baseline['strategy_receipts']==[]
catalog=strategy['execution_comparisons'];assert catalog['metadata_only']
assert any(row['id']==identity and not row['inputs_verified_now'] for row in catalog['comparisons'])
reserved=get('/api/chat')['reserved']
save('audit.json',{'method':'stdlib Decimal, CSV and UTC times; no comparator/engine imports','independent_rows':independent,
    'synthetic_example_only':True,'external_provider_chosen':'JForex / Dukascopy','real_external_report_supplied':False,
    'browser_preview_and_separate_save_verified':True,'saved_detail_reload_verified':True,'archived_inputs_verified':True,
    'manual_account_states_and_chains_preserved':True,'strategy_accounts_and_inbox_unchanged':True,
    'reserved_before':baseline['reserved'],'reserved_after':reserved,'own_model_requests':0,'new_backtests':0,
    'user_messages_copied':False,'account_operations':0,'external_orders_sent':False})
cases=ET.parse(out/'tests-final.xml').findall('.//testcase');counts=Counter(case.attrib['classname'] for case in cases)
assert len(cases)==630 and counts['tests.test_execution_comparison']==44 and all(not list(case) for case in cases)
assert '630 passed' in (out/'tests-final.log').read_text(encoding='utf-8')
subprocess.run(['C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe','--check','trading_ai/lab_static/simulation.js'],cwd=root,check=True,capture_output=True)
subprocess.run(['git','diff','--check'],cwd=root,check=True,capture_output=True)
for name in ('ui-execution-comparison.jpg','ui-execution-pairs.jpg','ui-execution-costs.jpg'):
    assert (out/name).read_bytes().startswith(b'\xff\xd8\xff')
sources=('trading_ai/execution_comparison.py','trading_ai/tv_service.py','trading_ai/lab_static/simulation.js','tests/test_execution_comparison.py')
for path in sources:put('tested-source/'+path,(root/path).read_bytes())
put('tested-source/collect-evidence.py',Path(__file__).read_bytes())
put('tested-source/prepare-fixture.py',(root/'.local/ev-data/prepare_execution_comparison.py').read_bytes())
manifest={'date':'2026-10-22','published_base_commit':protocol['published_base_commit'],'comparison':identity,
    'phase_closed':False,'this_increment_committed':False,'this_increment_pushed':False,'tests_passed':630,'new_comparison_tests':44,
    'full_suite_run':False,'test_counts':dict(counts),'javascript_syntax_checked':True,'git_diff_whitespace_checked':True,
    'protocol_sha256':digest(out/'protocol.json'),'prior_evidence_verified':prior,
    'source_sha256':{path:digest(root/path) for path in sources},'unchanged_prior_source_sha256':unchanged,
    'original_price_sha256':prices,'own_model_requests':0,'new_backtests':0,'account_operations':0,
    'synthetic_example_only':True,'real_external_equivalence_pending':True,'external_provider_chosen':'JForex / Dukascopy',
    'project_status_edited_this_increment':False,'external_orders_sent':False,'user_messages_copied':False,
    'evidence_sha256':{path.relative_to(out).as_posix():digest(path) for path in sorted(out.rglob('*')) if path.is_file() and path!=out/'manifest.json'}}
save('manifest.json',manifest)
for name,expected in manifest['evidence_sha256'].items():assert digest(out/name)==expected
print(json.dumps({'tests_passed':630,'new_comparison_tests':44,'prior_manifests_verified':len(prior),
    'evidence_files':len(manifest['evidence_sha256']),'manifest_sha256':digest(out/'manifest.json')},indent=2))

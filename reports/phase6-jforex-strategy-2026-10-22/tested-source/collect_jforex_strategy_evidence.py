"""Independent archive and audit. No project imports, model, engine or POST."""
from collections import Counter
import csv
from datetime import datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

root=Path(__file__).resolve().parents[2];out=root/'reports/phase6-jforex-strategy-2026-10-22'
def digest(path):return sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def checksum(value):return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def csv_rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def put(name,raw):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,name
    else:
        with path.open('xb') as stream:stream.write(raw)
def save(name,value):put(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
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
    for name,expected in entries.items():
        target=(path.parent/name).resolve();assert target.is_relative_to(root)
        assert digest(target)==expected,(path,name)
    prior[path.relative_to(root).as_posix()]={'sha256':digest(path),'files_verified':len(entries)}
assert len(prior)==15 and len({p.split('/')[1] for p in prior})==14
previous=read(root/'reports/phase6-jforex-preparation-2026-10-22/manifest.json')
unchanged=previous['unchanged_prior_source_sha256']
for name,expected in unchanged.items():assert digest(root/name)==expected,name
assert digest(root/'docs/PROJECT_STATUS.md')=='9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb'
for ref in ('HEAD','origin/main'):
    assert subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip()==previous['published_base_commit']
prices=read(root/'reports/phase6-execution-comparison-2026-10-22/manifest.json')['original_price_sha256']
for name,expected in prices.items():assert digest(Path('C:/Users/34656/Downloads')/name)==expected
protocol=read(out/'protocol.json');link=read(out/'reference-link.json')
old=read(root/'.local/dukascopy-research'/protocol['original_reference']/'simulation.json')
source=root/'.local/dukascopy-research'/link['id'];reference=read(source/'simulation.json');daily=read(source/'input-daily.json')
for result in (old,reference):assert checksum({k:v for k,v in result.items() if k!='result_sha256'})==result['result_sha256']
assert reference['result_sha256']==link['result_sha256'] and old['result_sha256']==protocol['original_reference_sha256']
assert reference['sessions_sha256']==old['sessions_sha256'] and reference['implementation_sha256']==old['implementation_sha256']
assert reference['observations']==old['observations'] and len(daily['sessions'])==307
for key,value in old['configuration'].items():
    assert reference['configuration'][key]==({'initial_capital':'1000000','quantity':'1000'}.get(key,value))
with localcontext(Context(prec=100)):
    for a,b in zip(old['hypothetical_fills'],reference['hypothetical_fills']):
        for key,value in a.items():
            if key in ('quantity','assumed_commission','spread_vs_midpoint'):assert Decimal(b[key])==Decimal(value)*1000
            else:assert b[key]==value
    assert len(old['hypothetical_fills'])==len(reference['hypothetical_fills'])==3
    for a,b in zip(old['equity_curve'],reference['equity_curve']):
        for key in ('cash','quantity','equity'):assert Decimal(b[key])==Decimal(a[key])*1000
    for key in ('initial_capital','final_equity','cash','open_quantity','assumed_commissions','realized_pnl'):
        assert Decimal(reference['summary'][key])==Decimal(old['summary'][key])*1000
for filename,key in [('input-manifest.json','manifest_sha256'),('input-daily.json','daily_file_sha256')]:
    assert digest(source/filename)==reference['source'][key]
for filename in ('simulation.json','input-manifest.json','input-daily.json'):put('python-reference/'+filename,(source/filename).read_bytes())

folders=list((root/'.local/jforex/sparse-offline-final-replay').glob('tiresias-test-*'));assert len(folders)==1
replay=folders[0];metadata=read(replay/'metadata.json')
assert metadata['engine_type']=='TEST' and metadata['declared_feed']=='offline_fixture_not_jforex_tester'
assert metadata['strategy_window_end_observed'] and not metadata['has_failure']
assert not metadata['external_equivalence_verified'] and not metadata['native_final_report_reconciled']
java_days=csv_rows(replay/'daily.csv');assert len(java_days)==len(reference['observations'])==307
for java_day,observation,day in zip(java_days,reference['observations'],daily['sessions']):
    assert java_day['date']==observation['date'] and java_day['signal']==observation['signal']
    assert java_day['boundary_observed']=='true' and java_day['tick_count']=='2'
    for key in ('fast','slow'):
        assert (None if java_day[key]=='' else Decimal(java_day[key]))==(None if observation[key] is None else Decimal(observation[key]))
    for side in ('bid','ask'):
        for key in ('open','close'):assert Decimal(java_day[side+'_'+key])==Decimal(day[side][key])
requests=[r for r in csv_rows(replay/'events.csv') if r['type'].endswith('_not_fill')]
executions=csv_rows(replay/'executions.csv');assert len(requests)==len(executions)==3
for request,execution,fill in zip(requests,executions,reference['hypothetical_fills']):
    assert request['type']==('buy_request_not_fill' if fill['side']=='buy' else 'close_request_not_fill')
    assert instant(request['at'])==instant(fill['executed_at']) and instant(request['signal_at'])==instant(fill['signal_at'])
    assert execution['side']==fill['side'] and instant(execution['executed_at'])==instant(fill['executed_at'])
    assert Decimal(execution['quantity'])==Decimal(fill['quantity'])==1000 and Decimal(execution['price'])==Decimal(fill['price'])
    assert execution['fee']==execution['external_id']==''
    assert execution['signal_binding']=='strategy_request_unverified_native_causality'
for path in sorted(replay.iterdir()):
    if path.is_file():put('offline-replay/'+path.name,path.read_bytes())
put('offline-replay/sparse-quotes.csv',(root/'.local/ev-data/jforex-sparse-quotes.csv').read_bytes())
replayed=read(out/'offline-replay-final.log');assert replayed['offline_api_doubles_only'] and not replayed['native_tester_run'] and not replayed['rejected']
api=Path('C:/Program Files/JForex4/libs/demo/4.9.8/jforex-api-4.9.8.jar')
assert digest(api)==protocol['local_api_jar_sha256']
classes=list((root/'.local/jforex/strategy-evidence-final-classes').glob('TiresiasSmaUtcTester*.class'));assert len(classes)>=4
for path in classes:assert int.from_bytes(path.read_bytes()[6:8],'big')==65
cases=ET.parse(out/'tests-final.xml').findall('.//testcase');counts=Counter(c.attrib['classname'] for c in cases)
assert len(cases)==660 and counts['tests.test_jforex_strategy']==30 and all(not list(c) for c in cases)
for name,count in read(root/'reports/phase6-execution-comparison-2026-10-22/manifest.json')['test_counts'].items():assert counts[name]==count
assert '660 passed' in (out/'tests-final.log').read_text(encoding='utf-8')

baseline=read(root/'.local/ev-data/execution-before.json')
manual=get('/api/chat/0190241d62b543c6b69b4a5db31051d6/manual-operations')
assert {a['id']:{'state':a['state'],'chain_sha256':a['chain_sha256']} for a in manual['accounts']}==baseline['manual_accounts']
simulation=get('/api/simulation');assert simulation['accounts']==simulation['receipts']==[]
reserved=get('/api/chat')['reserved'];before=read(root/'.local/ev-data/jforex-strategy-before.json')['reserved']
save('audit.json',{'method':'independent stdlib CSV, Decimal, UTC and SHA256; no project imports',
    'prior_manifests_verified':15,'prior_report_folders_verified':14,'core_sources_preserved':True,
    'original_prices_and_old_reference_preserved':True,'same_session_sma_and_request_times_verified':307,
    'sparse_offline_replay_only':True,'replay_fills_and_fees_artificial':True,'native_jforex_engine_used':False,
    'native_platform_compilation_verified':False,'external_report_supplied':False,'external_equivalence_verified':False,
    'new_local_research_backtests':1,'new_native_backtests':0,'own_model_requests':0,'reserved_before':before,'reserved_after':reserved,
    'existing_manual_accounts_preserved':True,'strategy_accounts_and_inbox_unchanged':True,'account_operations':0,
    'credentials_read_or_stored':False,'external_orders_sent':False,'user_messages_copied':False})
sources=('integrations/jforex/TiresiasSmaUtcTester.java','integrations/jforex/README.md','tests/jforex/JForexHarness.java','tests/test_jforex_strategy.py')
for name in sources:put('tested-source/'+name,(root/name).read_bytes())
for name in ('prepare_jforex_strategy_reference.py','replay_jforex_reference.py','collect_jforex_strategy_evidence.py'):
    put('tested-source/'+name,(root/'.local/ev-data'/name).read_bytes())
put('package/TiresiasSmaUtcTester.java',(root/'integrations/jforex/TiresiasSmaUtcTester.java').read_bytes())
put('package/README.md',(root/'integrations/jforex/README.md').read_bytes())
save('package/csv-mapping.json',read(root/'reports/phase6-execution-comparison-2026-10-22/protocol.json')['mapping'])
save('package/test-settings.json',{'protocol':'tiresias_jforex_test_preparation_v1','origin':'source_and_python_reference_not_external_report',
    'reference_run':link['id'],'reference_sha256':link['result_sha256'],'java_source_sha256':digest(root/'integrations/jforex/TiresiasSmaUtcTester.java'),
    'tester_currency':'USD','tester_initial_capital':'1000000','tester_leverage':'1','quantity_eur':'1000',
    'fast':20,'slow':60,'start_date':'2025-01-01','end_date_exclusive':'2025-12-25',
    'tester_sample_start_utc':'2025-01-01T00:00:00Z','tester_sample_end_utc':'2025-12-27T00:00:00Z',
    'declared_feed':'candles_h1_4ohlc_bid','native_platform_compilation_verified':False,'native_platform_run_verified':False,
    'external_equivalence_verified':False,'per_execution_fees_unknown':True,'api_dependency_redistributed':False})
put('package/python-reference.json',(source/'simulation.json').read_bytes())
package={'files_sha256':{p.relative_to(out/'package').as_posix():digest(p) for p in sorted((out/'package').iterdir()) if p.is_file() and p.name!='package-manifest.json'}}
save('package/package-manifest.json',package)
archive=out/'jforex-strategy.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as zipped:
    for path in sorted((out/'package').iterdir()):zipped.write(path,path.name)
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    for name,expected in package['files_sha256'].items():assert sha256(zipped.read(name)).hexdigest()==expected
subprocess.run(['git','diff','--check'],cwd=root,check=True,capture_output=True)
manifest={'date':'2026-10-22','published_base_commit':previous['published_base_commit'],'phase_closed':False,
    'this_increment_committed':False,'this_increment_pushed':False,'tests_passed':660,'new_jforex_tests':30,'full_suite_run':False,
    'test_counts':dict(counts),'installed_api_version':'4.9.8','installed_api_jar_sha256':digest(api),
    'javac_release':21,'compiled_class_sha256':{p.name:digest(p) for p in classes},'native_platform_compile_or_run_verified':False,
    'new_reference':link['id'],'new_local_research_backtests':1,'new_native_backtests':0,'own_model_requests':0,
    'external_orders_sent':False,'external_equivalence_pending':True,'source_sha256':{p:digest(root/p) for p in sources},
    'unchanged_prior_source_sha256':unchanged,'prior_evidence_verified':prior,
    'evidence_sha256':{p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}}
save('manifest.json',manifest)
for name,expected in manifest['evidence_sha256'].items():assert digest(out/name)==expected
print(json.dumps({'tests_passed':660,'new_jforex_tests':30,'prior_manifests_verified':15,'same_session_sma_verified':307,
    'native_jforex_run':False,'new_python_reference':link['id'],'package_bytes':archive.stat().st_size,
    'evidence_files':len(manifest['evidence_sha256']),'manifest_sha256':digest(out/'manifest.json')},indent=2))

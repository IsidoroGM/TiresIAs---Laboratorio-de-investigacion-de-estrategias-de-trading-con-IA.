"""Archive preparation only: no engine, credentials, installer execution or POSTs."""
from hashlib import sha256
from http.client import HTTPConnection
import csv
import io
import json
from pathlib import Path
import subprocess
import zipfile

root=Path(__file__).resolve().parents[2]
out=root/'reports/phase6-jforex-preparation-2026-10-22'
out.mkdir(exist_ok=True)
run='72061a4aa7a0455cb400edcc580cb964'
session='0190241d62b543c6b69b4a5db31051d6'
def digest(path):return sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def checksum(value):return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
def put(name,raw):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,name
    else:
        with path.open('xb') as stream:stream.write(raw)
def save(name,value):put(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def get(path):
    conn=HTTPConnection('127.0.0.1',64162,timeout=10)
    try:
        conn.request('GET',path);r=conn.getresponse();assert r.status==200
        return json.loads(r.read())
    finally:conn.close()
def state():
    manual=get('/api/chat/'+session+'/manual-operations');strategy=get('/api/simulation')
    return {'manual':{a['id']:{'state':a['state'],'chain':a['chain_sha256']} for a in manual['accounts']},
        'strategy_accounts':strategy['accounts'],'receipts':strategy['receipts'],'reserved':get('/api/chat')['reserved']}
before=state()
prior={}
for path in sorted((root/'reports').rglob('manifest.json')):
    if path.is_relative_to(out):continue
    entries=read(path).get('evidence_sha256')
    if not isinstance(entries,dict):continue
    for relative,expected in entries.items():
        target=(path.parent/relative).resolve();assert target.is_relative_to(root)
        assert digest(target)==expected,(path,relative)
    prior[path.relative_to(root).as_posix()]={'sha256':digest(path),'files_verified':len(entries)}
assert len(prior)==14,len(prior)
assert len({name.split('/')[1] for name in prior})==13
previous=read(root/'reports/phase6-execution-comparison-2026-10-22/manifest.json')
unchanged=previous['unchanged_prior_source_sha256']|previous['source_sha256']
for path,expected in unchanged.items():assert digest(root/path)==expected,path
assert digest(root/'docs/PROJECT_STATUS.md')=='9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb'
for ref in ('HEAD','origin/main'):
    assert subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip()==previous['published_base_commit']
reference_dir=root/'.local/dukascopy-research'/run
reference=read(reference_dir/'simulation.json')
assert checksum({key:value for key,value in reference.items() if key!='result_sha256'})==reference['result_sha256']=='69b7208f21a53d1f6b6c7ffe60d00c303fdbcba22f9ebdb18f9b82a1115375c0'
assert reference['configuration']['quantity']=='1' and reference['configuration']['initial_capital']=='1000'
assert len(reference['hypothetical_fills'])==3 and reference['daily_sessions']==307
for filename,key in [('input-manifest.json','manifest_sha256'),('input-daily.json','daily_file_sha256')]:
    assert digest(reference_dir/filename)==reference['source'][key]
for name,expected in previous['original_price_sha256'].items():
    assert digest(Path('C:/Users/34656/Downloads')/name)==expected
downloads=root/'.local/jforex/downloads'
download=read(downloads/'JForex4_windows-x64.download.json');signature=read(downloads/'signature.json')
assert digest(downloads/'JForex4_windows-x64.exe')==download['sha256']=='de97aa5ca691a8f027a07da466a146022c8a05a7d327f0a887d626d2f81667e4'
assert (downloads/'JForex4_windows-x64.exe').stat().st_size==download['bytes']==70667784
assert download['url']==download['final_url']=='https://platform.dukascopy.com/jforex4-installer/JForex4_windows-x64.exe'
assert signature['status']=='Valid' and signature['subject'].startswith('CN=SWFX SA,') and signature['product_version']=='4.23'
save('installer-download.json',download);save('installer-signature.json',signature)
configuration={'protocol':'tiresias_jforex_preparation_v1','date':'2026-10-22','status':'pending_installation_access_strategy_and_external_run',
    'reference_run':run,'reference_sha256':reference['result_sha256'],'reference_configuration':reference['configuration'],
    'start_date':reference['source']['start_date'],'end_date_exclusive':reference['source']['end_date_exclusive'],
    'sessions_sha256':reference['sessions_sha256'],'origin':'python_reference_not_external_report',
    'reference_daily_sessions':307,'reference_fills':3,'jforex_found_in_standard_locations':False,'portable_installation_ruled_out':False,
    'api_eurusd_minimum_units_documented':'1000','api_amount_unit':'million_base_units','current_quantity_reproducible_under_documented_minimum':False,
    'proposed_new_case':{'status':'proposed_not_calculated','initial_capital_usd':'1000000','quantity_eur':'1000','jforex_api_amount_millions':'0.001',
        'scale_from_old_reference':'1000','assumed_commission_rate':'0.001','provider_fee_equivalence_verified':False,'original_reference_replaced':False},
    'execution_mode_required':'IEngine.Type.TEST','java_strategy_prepared':False,'java_strategy_compiled':False,'java_strategy_run':False,
    'native_daily_candles_equivalent':None,'actual_provider_fees_known':False,'external_report_supplied':False,
    'external_equivalence_verified':False,'new_backtests':0,'account_operations':0,'own_model_requests':0,'external_orders_sent':False}
save('bundle/configuration.json',configuration)
for filename in ('simulation.json','input-manifest.json','input-daily.json'):
    put('bundle/python-reference/'+filename,(reference_dir/filename).read_bytes())
stream=io.StringIO(newline='')
writer=csv.writer(stream);writer.writerow(['python_reference_index','side','executed_at','signal_at','quantity_eur','price_usd_per_eur','assumed_fee_usd'])
for i,fill in enumerate(reference['hypothetical_fills'],1):
    writer.writerow([i,fill['side'],fill['executed_at'],fill['signal_at'],fill['quantity'],fill['price'],fill['assumed_commission']])
put('bundle/python-reference/fills.csv',stream.getvalue().encode('utf-8'))
put('bundle/JFOREX_SETUP.md',(root/'docs/JFOREX_SETUP.md').read_bytes())
package_manifest={'protocol':'tiresias_jforex_preparation_v1','origin':'python_reference_not_external_report',
    'evidence_sha256':{p.relative_to(out/'bundle').as_posix():digest(p) for p in sorted((out/'bundle').rglob('*')) if p.is_file() and p.name!='package-manifest.json'}}
save('bundle/package-manifest.json',package_manifest)
archive=out/'jforex-preparation.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as zipped:
    for p in sorted((out/'bundle').rglob('*')):
        if p.is_file():zipped.write(p,p.relative_to(out/'bundle').as_posix())
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    for name,expected in package_manifest['evidence_sha256'].items():assert sha256(zipped.read(name)).hexdigest()==expected
after=state();assert after==before
save('audit.json',{'prior_manifests_verified':14,'prior_report_folders_verified':13,'source_hashes_preserved':True,'reference_copies_verified':True,'zip_crc_and_file_hashes_verified':True,
    'installer_not_launched_by_preparation':True,'installer_signed_by':'SWFX SA','installer_signature_observed':'Valid',
    'application_code_changed_this_increment':False,'new_application_tests_run':False,'prior_selected_tests_passed':630,
    'application_and_manual_accounts_unchanged_during_preparation':True,'reserved_before':before['reserved'],'reserved_after':after['reserved'],
    'own_model_requests':0,'new_backtests':0,'account_operations':0,'account_registration_submitted':False,
    'credentials_read_or_stored':False,'external_orders_sent':False,'external_report_supplied':False,
    'new_scaled_case_calculated':False,'jforex_strategy_prepared':False,'project_status_edited':False})
for name in ('download_jforex_setup.py','prepare_jforex_evidence.py'):
    put('preparation-source/'+name,(root/'.local/ev-data'/name).read_bytes())
subprocess.run(['git','diff','--check'],cwd=root,check=True,capture_output=True)
manifest={'date':'2026-10-22','phase_closed':False,'published_base_commit':previous['published_base_commit'],
    'this_increment_committed':False,'this_increment_pushed':False,'preparation_only':True,'application_code_changed':False,
    'new_tests_run':False,'new_backtests':0,'own_model_requests':0,'external_orders_sent':False,
    'external_equivalence_pending':True,'installer_executed':False,'prior_evidence_verified':prior,
    'unchanged_prior_source_sha256':unchanged,'evidence_sha256':{p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}}
save('manifest.json',manifest)
print(json.dumps({'prior_manifests_verified':14,'prior_report_folders_verified':13,'reference_prepared':run,'installer_signature':'Valid','evidence_files':len(manifest['evidence_sha256']),
    'package_bytes':archive.stat().st_size,'manifest_sha256':digest(out/'manifest.json')},indent=2))

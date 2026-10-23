"""One explicit local reference, independent of chat/model budgets and accounts."""
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from trading_ai.dukascopy_service import DukascopyResearch

out=root/'reports/phase6-jforex-strategy-2026-10-22';out.mkdir(exist_ok=True)
old_id='72061a4aa7a0455cb400edcc580cb964'
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
service=DukascopyResearch(root);old=service.get(old_id)
assert old['configuration']['initial_capital']=='1000' and old['configuration']['quantity']=='1'
api=Path('C:/Program Files/JForex4/libs/demo/4.9.8/jforex-api-4.9.8.jar')
protocol={'date':'2026-10-22','user_confirms_jforex_and_demo_access':True,'observed_installation_version':'4.23',
    'local_api_version':'4.9.8','local_api_jar_sha256':sha256(api.read_bytes()).hexdigest(),
    'original_reference':old_id,'original_reference_sha256':old['result_sha256'],
    'new_reference_parameters':{'dataset':Path(old['source']['directory']).name,'capital':'1000000','quantity':'1000','commission_rate':'0.001'},
    'strategy_interval_utc':{'start_date':'2025-01-01','end_date_exclusive':'2025-12-25'},
    'comparison_scope':'same fixed SMA20/60 rules and original prices; no optimization',
    'java_validation':'compile against installed API, run interface doubles offline, replay same fixed daily prices',
    'native_jforex_tester_run_by_agent':False,'native_jforex_compilation_verified':False,
    'external_report_supplied':False,'new_local_research_backtests_authorized':1,'own_model_requests':0,
    'account_operations':0,'external_orders_sent':False,'phase_closed':False,'commit_or_push_authorized_this_increment':False}
assert not (out/'protocol.json').exists()
save(out/'protocol.json',protocol)
connection=HTTPConnection('127.0.0.1',64162,timeout=10)
connection.request('GET','/api/chat');response=connection.getresponse();assert response.status==200
save(root/'.local/ev-data/jforex-strategy-before.json',{'reserved':json.loads(response.read())['reserved']});connection.close()
result=service.run(**protocol['new_reference_parameters'])
reference=service.get(result['id']);assert reference['status']=='simulated'
assert reference['sessions_sha256']==old['sessions_sha256']
assert reference['configuration']['fast']==20 and reference['configuration']['slow']==60
save(out/'reference-link.json',{'id':result['id'],'result_sha256':reference['result_sha256'],'parameters':protocol['new_reference_parameters'],
    'origin':'new_python_backtest_on_preserved_prices_not_external_report','old_reference_unchanged':service.get(old_id)==old})
print(json.dumps({'new_reference':result['id'],'result_sha256':reference['result_sha256'],'sessions':reference['daily_sessions'],
    'fills':len(reference['hypothetical_fills']),'new_local_backtests':1,'external_backtests':0,'own_model_requests':0}))

"""La pantalla de simulación consulta sin efectos y exige revisar cada acción."""

import base64
from contextlib import contextmanager
from http.client import HTTPConnection
import json
import threading

import pytest

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.lab import create_server
from trading_ai.tv_contracts import canonical, checksum, make_contract
from trading_ai.tv_io import import_lock
from trading_ai.tv_service import SimulationService
from trading_ai.tv_simulation import RISK


@pytest.fixture
def setup(tmp_path):
    service=SimulationService(tmp_path)
    c=make_contract(fast=2,slow=3,ticker='SYNTH:EURUSD',start='2020-01-01T00:00:00Z',end='2021-01-01T00:00:00Z',capital='100',cost_rate='0.01')
    service.action({'action':'prepare_bundle','contract':c})
    service.action({'action':'register','bundle':checksum(c),'risk':dict(RISK),'approve_virtual_account':True})
    return service,c,checksum(c)


def event(c,sequence=1,side='buy'):
    return {'protocol':'tiresias_simulated_fill_v1','contract_sha256':checksum(c),'execution_id':'test-'+str(sequence),'sequence':sequence,
            'side':side,'quantity':'1','price':'10','fee':None,'currency':'USD',
            'signal_at':f'2020-01-{sequence:02d}T23:00:00Z','executed_at':f'2020-01-{sequence+1:02d}T00:00:00Z'}


def review(service,account):
    state=service.get('accounts',account)
    return {'action':'process','account':account,'chain_sha256':state['chain_sha256'],'review_sha256':state['review_sha256'],'approve_processing':True}


def test_queries_do_not_initialize_or_call_the_model(tmp_path):
    service=SimulationService(tmp_path)
    overview=service.overview()
    assert overview['supported_pairs']==list(SUPPORTED_PAIRS)
    assert not overview['external_connection'] and not (tmp_path/'.local').exists()


def test_new_pending_execution_invalidates_review_even_if_cash_is_unchanged(setup):
    service,c,account=setup
    service.ledger.receive(canonical(event(c)));approval=review(service,account)
    service.ledger.receive(canonical(event(c,2,'sell')))
    with pytest.raises(ValueError,match='inbox cambió'):service.action(approval)
    assert service.ledger.account(account)['state']['cash']=='100'
    result=service.action(review(service,account))
    assert result['applied']==['test-1','test-2']
    assert service.ledger.account(account)['state']['cash']=='99.8'
    with pytest.raises(ValueError,match='cuenta cambió'):service.action(approval)


def test_changed_mark_invalidates_processing_and_null_hash_cannot_bypass_review(setup):
    service,c,account=setup
    service.ledger.receive(canonical(event(c)));approval=review(service,account)
    service.ledger.mark(account,price='10',at='2020-01-01T00:00:00Z',mark_id='m1')
    with pytest.raises(ValueError,match='cuenta cambió'):service.action(approval)
    approval=review(service,account)
    for key in ('chain_sha256','review_sha256'):
        with pytest.raises(ValueError):service.action({**approval,key:None})
    assert service.ledger.account(account)['state']['cash']=='100'


def test_new_conflict_invalidates_review_and_is_visible_before_processing(setup):
    service,c,account=setup
    service.ledger.receive(canonical(event(c)));approval=review(service,account)
    service.ledger.receive(canonical({**event(c),'price':'11'}))
    with pytest.raises(ValueError,match='inbox cambió'):service.action(approval)
    current=service.ledger.account(account)
    assert current['problem_count']==1 and current['problem_receipts'][0]['state']=='conflict'
    assert current['state']['cash']=='100'


@pytest.mark.parametrize('action',[
    {'action':'register','bundle':'0'*64,'risk':dict(RISK),'approve_virtual_account':False},
    {'action':'receive','raw':'{}','approve_inbox':False},
    {'action':'process','account':'0'*64,'chain_sha256':'0'*64,'review_sha256':'0'*64,'approve_processing':False},
    {'action':'buy_now','account':'0'*64},
    {'action':'prepare_bundle','contract':{},'path':'../../outside'},
])
def test_missing_review_or_arbitrary_actions_have_no_effect(tmp_path,action):
    service=SimulationService(tmp_path)
    with pytest.raises(ValueError):service.action(action)
    assert not (tmp_path/'.local').exists()


def test_csv_preview_and_import_keep_exact_original_bytes(setup,tmp_path):
    service,c,account=setup;mapping=service.overview()['mapping_template']
    raw=(b'\xef\xbb\xbfexecution_id,sequence,side,quantity,price,fee,signal_at,executed_at\r\n'
         b'file-1,1,buy,1,10,0.1,2020-01-01T23:00:00Z,2020-01-02T00:00:00Z\r\n')
    request={'action':'preview_csv','bundle':account,'csv_base64':base64.b64encode(raw).decode(),'mapping':mapping}
    preview=service.action(request);assert not preview['preview']['errors']
    result=service.action({**request,'action':'import_csv','approve_preview_sha256':preview['approval_sha256']})
    assert (tmp_path/'.local'/'tradingview-imports'/result['id']/'original.csv').read_bytes()==raw
    assert service.ledger.account(account)['state']['cash']=='100'
    assert service.action(review(service,account))['applied']==['file-1']


def test_import_lock_prevents_a_second_process_writer(tmp_path):
    with import_lock(tmp_path):
        with pytest.raises(ValueError,match='segundo escritor'):
            with import_lock(tmp_path):pass
    with import_lock(tmp_path):pass


def request(server,path='/api/simulation',body=None,headers=None):
    connection=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
    try:
        connection.request('POST' if body is not None else 'GET',path,body=body,headers=headers or {})
        response=connection.getresponse();raw=response.read()
        return response.status,json.loads(raw) if response.getheader('Content-Type','').startswith('application/json') else raw
    finally:connection.close()


@pytest.fixture
def http(tmp_path):
    server=create_server(root=tmp_path,port=0,refresh_interval=60)
    thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.05});thread.start()
    try:yield server,tmp_path
    finally:server.shutdown();thread.join(timeout=5);server.server_close()


def test_http_gets_and_static_assets_do_not_create_virtual_accounts(http):
    server,root=http
    for path in ('/api/simulation','/simulation.js','/simulation.css','/'):
        assert request(server,path)[0]==200
    assert not (root/'.local').exists()


@pytest.mark.parametrize('change',[{'Origin':'https://evil.test'},{'Origin':'null'},{'X-Tiresias-Action':'wrong'},{'X-Tiresias-Action':'inválido'},{'Sec-Fetch-Site':'cross-site'},{'Host':'evil.test'}])
def test_simulation_actions_use_the_same_origin_security_boundary(http,change):
    server,root=http;overview=request(server)[1]
    headers={'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json','X-Tiresias-Action':overview['action_token'],**change}
    assert request(server,body='{"action":"prepare_bundle","contract":{}}',headers=headers)[0]==403
    assert not (root/'.local').exists()


def test_http_contract_preparation_is_explicit_and_rejects_duplicate_keys(http):
    server,root=http;overview=request(server)[1]
    headers={'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json','X-Tiresias-Action':overview['action_token']}
    assert request(server,body='{"action":"prepare_bundle","action":"register"}',headers=headers)[0]==422
    c=make_contract();status,result=request(server,body=canonical({'action':'prepare_bundle','contract':c}),headers=headers)
    assert status==202 and result['id']==checksum(c)
    assert not (root/'.local'/'simulation').exists()
    assert request(server,'/api/simulation/bundles/'+result['id'])[1]['contract']==c
    assert request(server,'/api/simulation/accounts/'+'0'*64)[0] in (404,422)


def test_http_deep_json_is_rejected_before_initializing_storage(http):
    server,root=http;overview=request(server)[1]
    headers={'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json','X-Tiresias-Action':overview['action_token']}
    status,result=request(server,body='{"action":"prepare_bundle","contract":'+'['*100+'0'+']'*100+'}',headers=headers)
    assert status==422 and 'profundo' in result['error']
    assert not (root/'.local').exists()

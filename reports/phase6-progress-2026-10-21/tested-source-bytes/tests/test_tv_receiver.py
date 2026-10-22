"""El acuse HTTP conserva bytes y nunca ejecuta una operación."""

from contextlib import contextmanager
from http.client import HTTPConnection
import threading

import pytest

from trading_ai.tv_contracts import canonical, checksum, make_contract
from trading_ai.tv_receiver import create_receiver
from trading_ai.tv_simulation import SimulationLedger


TOKEN = 'test-only-' + 'x'*32


@contextmanager
def server(ledger):
    receiver=create_receiver(ledger,token=TOKEN,port=0)
    worker=threading.Thread(target=receiver.serve_forever,kwargs={'poll_interval':0.05});worker.start()
    try:yield receiver
    finally:receiver.shutdown();worker.join(timeout=5);receiver.server_close()


def request(receiver,body=b'{bad',*,headers=None,method='POST',path='/events'):
    conn=HTTPConnection('127.0.0.1',receiver.server_port,timeout=3)
    conn.request(method,path,body=body,headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json',**(headers or {})})
    response=conn.getresponse();raw=response.read();conn.close()
    return response.status,raw


def test_receipt_acknowledges_commit_without_processing_and_survives_restart(tmp_path):
    ledger=SimulationLedger(tmp_path);c=make_contract();account=ledger.register(c)['account']
    event={'protocol':'tiresias_simulated_fill_v1','contract_sha256':account,'execution_id':'test-buy','sequence':1,
           'side':'buy','quantity':'1','price':'1.2','fee':None,'currency':'USD',
           'signal_at':'2025-01-01T00:00:00Z','executed_at':'2025-01-02T00:00:00Z'}
    with server(ledger) as receiver:
        status,raw=request(receiver,canonical(event))
        assert status==202 and b'"accounting_processed":false' in raw
        assert ledger.account(account)['state']['cash']=='1000'
        assert request(receiver,canonical(event))[0]==202
    again=SimulationLedger(tmp_path)
    assert len(again.overview()['receipts'])==2
    assert again.process(account)['applied']==['test-buy']
    assert again.account(account)['state']['filled_orders']==1


@pytest.mark.parametrize('headers,status',[
    ({'Authorization':'Bearer wrong'},401),({'Content-Type':'text/plain'},415),
    ({'Content-Length':'65537'},413),({'Transfer-Encoding':'chunked'},400),
    ({'Content-Length':'-1'},400),({'Origin':'https://example.test'},403),({'Host':'evil.test'},403),
])
def test_rejected_transport_does_not_create_storage(tmp_path,headers,status):
    ledger=SimulationLedger(tmp_path)
    with server(ledger) as receiver:assert request(receiver,headers=headers)[0]==status
    assert not ledger.path.exists()


def test_invalid_original_is_durable_but_never_an_execution(tmp_path):
    ledger=SimulationLedger(tmp_path)
    with server(ledger) as receiver:
        status,raw=request(receiver)
        assert status==202 and b'"state":"invalid"' in raw
    receipt=ledger.overview()['receipts'][0]
    assert ledger.receipt(receipt['id'])['raw']=='{bad'


def test_failed_commit_is_not_acknowledged(tmp_path,monkeypatch):
    ledger=SimulationLedger(tmp_path)
    def failed(*args,**kwargs):raise ValueError('private/path/secret')
    monkeypatch.setattr(ledger,'receive',failed)
    with server(ledger) as receiver:
        status,raw=request(receiver)
        assert status==503 and b'private' not in raw and TOKEN.encode() not in raw


def test_methods_routes_and_missing_auth_are_closed(tmp_path):
    ledger=SimulationLedger(tmp_path)
    with server(ledger) as receiver:
        assert request(receiver,method='GET')[0]==405
        assert request(receiver,path='/events?token='+TOKEN)[0]==404
        assert request(receiver,headers={'Authorization':''})[0]==401
    assert not ledger.path.exists()


@pytest.mark.parametrize('token',['', 'x'*31, 'x'*129, 'secret token with spaces'+'x'*32])
def test_requires_explicit_strong_local_token(tmp_path,token):
    with pytest.raises(ValueError):create_receiver(SimulationLedger(tmp_path),token=token,port=0)

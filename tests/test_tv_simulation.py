"""Contabilidad independiente de IA, recepción duradera y recuperación sin duplicados."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from decimal import localcontext
import json
from pathlib import Path
import sqlite3

import pytest

from trading_ai.tv_contracts import canonical, checksum, make_contract, milliseconds
from trading_ai.tv_simulation import RISK, SimulationLedger, normalize_pine


@pytest.fixture
def ledger(tmp_path):
    c=make_contract(fast=2,slow=3,ticker="SYNTH:EURUSD",start="2020-01-01T00:00:00Z",end="2021-01-01T00:00:00Z",capital="100",cost_rate="0.01")
    result=SimulationLedger(tmp_path);account=result.register(c)['account']
    return result,c,account


def fill(c,seq=1,side='buy',**changes):
    return {'protocol':'tiresias_simulated_fill_v1','contract_sha256':checksum(c),'execution_id':'execution-'+str(seq),
            'sequence':seq,'side':side,'quantity':'1','price':'10' if side=='buy' else '12','fee':None,
            'currency':'USD','signal_at':f'2020-01-{seq:02d}T23:00:00Z','executed_at':f'2020-01-{seq+1:02d}T00:00:00Z',**changes}


def submit(ledger,c,**changes):return ledger.receive(canonical(fill(c,**changes)))


def test_receiving_is_durable_but_does_not_execute(ledger):
    store,c,account=ledger
    receipt=submit(store,c)
    assert receipt['state']=='queued'
    assert store.account(account)['state']['cash']=='100'
    again=SimulationLedger(store.root)
    assert again.receipt(receipt['receipt'])['raw']==canonical(fill(c)).decode()
    assert again.process(account)['applied']==['execution-1']
    assert again.account(account)['state']['cash']=='89.9'


def test_cash_quantity_costs_and_realized_are_exact_once(ledger):
    store,c,account=ledger
    submit(store,c);store.process(account)
    store.mark(account,price='12',at='2020-01-02T23:00:00Z',mark_id='m1')
    submit(store,c,seq=2,side='sell');store.process(account)
    state=store.account(account)['state']
    assert state['cash']==state['equity']=='101.78'
    assert state['realized_pnl']=='1.78'
    assert state['fees']=='0.22'
    assert state['quantity']=='0'
    assert state['estimated_fee_events']==2
    assert not state['risk_paused']
    assert store.process(account)['applied']==[]


def test_repeated_webhook_and_import_share_one_execution_identity(ledger):
    store,c,account=ledger
    raw=canonical(fill(c))
    assert store.receive(raw,transport='authenticated_webhook')['state']=='queued'
    assert store.receive(raw,transport='file_import')['state']=='duplicate'
    assert len(store.overview()['receipts'])==2
    store.process(account)
    assert store.receive(raw)['state']=='duplicate'
    assert store.account(account)['state']['filled_orders']==1


@pytest.mark.parametrize('changes',[{'price':'11'},{'execution_id':'other'},{'quantity':'2'},{'fee':'0.9'}])
def test_conflicts_are_saved_without_overwriting_original(ledger,changes):
    store,c,account=ledger
    submit(store,c)
    assert submit(store,c,**changes)['state']=='conflict'
    store.process(account)
    assert store.account(account)['state']['cash']=='89.9'


def test_gap_waits_then_processes_in_source_order(ledger):
    store,c,account=ledger
    submit(store,c,seq=2,side='sell')
    assert store.process(account)['applied']==[]
    assert store.account(account)['waiting_for_sequence']==1
    submit(store,c)
    assert store.process(account)['applied']==['execution-1','execution-2']
    assert store.account(account)['waiting_for_sequence'] is None


@pytest.mark.parametrize('changes,reason',[({'quantity':'2'},'quantity_limit'),({'price':'200'},'insufficient_cash'),({'fee':'0.9'},'fee_discrepancy'),({'side':'sell'},'insufficient_position')])
def test_risk_rejections_leave_capital_unchanged_and_pause_new_entries(ledger,changes,reason):
    store,c,account=ledger
    submit(store,c,**changes)
    assert store.process(account)['rejected']==['execution-1']
    state=store.account(account)['state']
    assert state['cash']=='100' and state['quantity']=='0'
    assert state['last_reason']==reason and state['risk_paused']
    submit(store,c,seq=2)
    assert store.process(account)['rejected']==['execution-2']


def test_risk_drawdown_blocks_buys_but_allows_exit(ledger):
    old,c,_=ledger
    c=deepcopy(c);c['account']['id']='risk-test'
    account=old.register(c,{**RISK,'max_drawdown_fraction':'0.05'})['account']
    submit(old,c);old.process(account)
    old.mark(account,price='1',at='2020-01-02T23:00:00Z',mark_id='down')
    assert old.account(account)['state']['risk_paused']
    submit(old,c,seq=2,side='sell',price='1')
    assert old.process(account)['applied']==['execution-2']
    submit(old,c,seq=3,price='1')
    assert old.process(account)['rejected']==['execution-3']


def test_mark_and_event_delays_are_not_silently_reordered(ledger):
    store,c,account=ledger
    submit(store,c);store.process(account)
    store.mark(account,price='12',at='2020-01-05T00:00:00Z',mark_id='recent')
    with pytest.raises(ValueError,match='atrasada'):store.mark(account,price='11',at='2020-01-04T00:00:00Z',mark_id='late')
    submit(store,c,seq=2,side='sell')
    assert store.process(account)['rejected']==['execution-2']
    assert store.account(account)['state']['last_reason']=='out_of_order_execution'


def test_marks_are_idempotent_and_prices_are_dated(ledger):
    store,c,account=ledger
    store.mark(account,price='12',at='2020-01-05T00:00:00Z',mark_id='one')
    assert store.mark(account,price='12',at='2020-01-05T00:00:00Z',mark_id='one')['duplicate']
    with pytest.raises(ValueError):store.mark(account,price='13',at='2020-01-05T00:00:00Z',mark_id='one')
    assert not store.account(account,as_of='2020-01-05T01:00:00Z')['price_stale']
    assert store.account(account,as_of='2020-01-10T00:00:00Z')['price_stale']


def test_reconcile_compares_without_replacing_capital(ledger):
    store,c,account=ledger
    submit(store,c);store.process(account)
    values={'as_of':'2020-01-02T00:00:00Z','currency':'USD','cash':'89.9','quantity':'1','equity':'99.9'}
    assert store.reconcile(account,values)['matches']
    report=store.reconcile(account,{**values,'cash':'10000'})
    assert not report['matches'] and not report['local_capital_replaced']
    assert store.account(account)['state']['cash']=='89.9'
    assert not store.reconcile(account,{**values,'cash':None})['matches']
    assert not store.reconcile(account,{**values,'as_of':'2020-01-03T00:00:00Z'})['comparable_at_same_time']
    with pytest.raises(ValueError):store.reconcile(account,{**values,'currency':'JPY'})


def test_account_currency_and_configuration_remain_independent(ledger):
    store,c,account=ledger
    other=make_contract(pair='USD/JPY',ticker='SYNTH:USDJPY')
    second=store.register(other)['account']
    submit(store,c);store.process(account)
    assert store.account(second)['state']['cash']=='1000'
    assert store.account(second)['contract']['account']['currency']=='JPY'
    assert store.register(c)['created'] is False
    with pytest.raises(ValueError):store.register(c,{**RISK,'max_orders':2})


def test_raw_invalid_and_unknown_events_are_retained(ledger):
    store,c,_=ledger
    for raw,state in [(b'{bad','invalid'),(b'{"x":1,"x":2}','invalid'),(canonical(fill(c,contract_sha256='f'*64)),'unknown_contract')]:
        receipt=store.receive(raw)
        assert receipt['state']==state
        assert store.receipt(receipt['receipt'])['raw']==raw.decode()


def test_pine_alert_uses_fill_price_not_signal_price(ledger):
    store,c,account=ledger
    value={'protocol':'tiresias_pine_fill_v1','contract_sha256':account,'ticker':'SYNTH:EURUSD','timeframe':'1D',
           'side':'buy','quantity':'1','price':'9','executed_at':'2020-01-02T00:00:00Z',
           'execution_time_basis':'bar_open_by_contract','alert_fired_at':'2020-01-02T00:00:05Z','currency':'USD',
           'order_meta':{'sequence':1,'execution_id':'TI-B-1','signal_time_ms':milliseconds('2020-01-01T23:00:00Z')}}
    event=normalize_pine(value,c)
    assert event['price']=='9' and event['fee'] is None
    assert event['executed_at']=='2020-01-02T00:00:00.000Z'
    with pytest.raises(ValueError):normalize_pine({**value,'alert_fired_at':'2020-01-01T00:00:00Z'},c)
    receipt=store.receive(canonical(value),transport='authenticated_webhook')
    assert receipt['state']=='queued'
    store.process(account)
    assert store.account(account)['state']['cash']=='90.91'


def test_tampered_event_and_posting_are_detected(ledger):
    store,c,account=ledger
    submit(store,c)
    with store.connection(True) as conn:conn.execute("UPDATE events SET data=?",(canonical(fill(c,price='20')).decode(),))
    with pytest.raises(ValueError,match='alterado'):store.process(account)
    with store.connection(True) as conn:conn.execute("UPDATE events SET data=?",(canonical(fill(c)).decode(),))
    store.process(account)
    with store.connection(True) as conn:conn.execute("UPDATE postings SET data='{}'")
    with pytest.raises(ValueError,match='alterada'):store.account(account)


def test_partial_chain_loss_is_detected(ledger):
    store,c,account=ledger
    submit(store,c);store.process(account)
    with store.connection(True) as conn:conn.execute('DELETE FROM postings')
    with pytest.raises(ValueError,match='secuencia'):store.account(account)


def test_get_overview_does_not_initialize_storage(tmp_path):
    assert SimulationLedger(tmp_path).overview()=={'accounts':[],'receipts':[]}
    assert not (tmp_path/'.local').exists()


def test_global_decimal_context_cannot_change_bookkeeping(ledger):
    store,c,account=ledger
    with localcontext() as ctx:
        ctx.prec=2
        submit(store,c);store.process(account)
        submit(store,c,seq=2,side='sell');store.process(account)
        assert store.account(account)['state']['cash']=='101.78'


def test_two_processors_cannot_book_the_same_review_twice(ledger):
    store,c,account=ledger;submit(store,c)
    state=store.account(account)
    def process(_):
        try:return SimulationLedger(store.root).process(account,expected_chain=state['chain_sha256'],expected_review=state['review_sha256'])
        except ValueError as error:return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(process,range(2)))
    assert sum(isinstance(result,dict) for result in results)==1
    assert store.account(account)['state']['filled_orders']==1
    assert store.account(account)['state']['cash']=='89.9'


def test_changed_engine_is_visible_and_blocks_actions_without_erasing_history(ledger,monkeypatch):
    store,c,account=ledger;submit(store,c);store.process(account)
    import trading_ai.tv_simulation as module
    monkeypatch.setattr(module,'engine_hashes',lambda:{'changed':'a'*64})
    assert not store.account(account)['engine_compatible']
    assert store.account(account)['state']['cash']=='89.9'
    with pytest.raises(ValueError,match='motor cambió'):store.process(account)
    with pytest.raises(ValueError,match='motor cambió'):store.mark(account,price='10',at='2020-01-03T00:00:00Z',mark_id='new')

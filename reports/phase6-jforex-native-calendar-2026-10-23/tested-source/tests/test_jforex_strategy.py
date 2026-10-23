"""Compile against the installed API and exercise doubles, never a native client."""
import csv
from datetime import datetime, timedelta, UTC
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import moving_average_crossover_signals

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def compiled(tmp_path_factory):
    candidates=list(Path('C:/Program Files/JForex4/libs/demo').glob('*/jforex-api-*.jar'))
    candidates=[p for p in candidates if not p.name.endswith('-sources.jar')]
    override=os.environ.get('TIRESIAS_JFOREX_API_JAR')
    api=Path(override) if override else max(candidates,key=lambda p:tuple(map(int,p.parent.name.split('.'))),default=None)
    java,javac=shutil.which('java'),shutil.which('javac')
    if api is None or not api.is_file() or not java or not javac:
        pytest.skip('Requires local JDK 21+ and the JForex API jar; does not download or connect')
    build=tmp_path_factory.mktemp('jforex-classes')
    command=[javac,'--release','21','-encoding','UTF-8','-cp',str(api),'-d',str(build),
        str(ROOT/'integrations/jforex/TiresiasSmaUtcTester.java'),str(ROOT/'tests/jforex/JForexHarness.java')]
    subprocess.run(command,cwd=ROOT,check=True,capture_output=True,text=True,timeout=40)
    return java,os.pathsep.join((str(build),str(api)))


@pytest.fixture(scope="module")
def scenarios(compiled,tmp_path_factory):
    root=tmp_path_factory.mktemp('jforex-cases')
    result=subprocess.run([compiled[0],'-cp',compiled[1],'JForexHarness','batch',str(root)],
        cwd=ROOT,check=True,capture_output=True,text=True,timeout=60)
    values={item['scenario']:item for item in map(json.loads,result.stdout.splitlines())}
    assert len(values)==34 and all(v['offline_api_doubles_only'] and not v['native_tester_run'] for v in values.values())
    return root,values


def exported(scenarios,name):
    folders=list((scenarios[0]/name).glob('tiresias-test-*'));assert len(folders)==1
    return folders[0]


def rows(folder,name):
    with (folder/name).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))


@pytest.mark.parametrize('name',['guard_live','guard_demo'])
def test_live_and_demo_blocked_before_files_subscription_or_orders(scenarios,name):
    value=scenarios[1][name]
    assert value['rejected'] and value['submissions']==value['closures']==value['file_queries']==value['subscriptions']==0
    assert value['calendar_queries']==0
    assert not list((scenarios[0]/name).iterdir())


def test_all_callbacks_recheck_the_tester_guard(scenarios):
    assert scenarios[1]['guard_callbacks']['submissions']==scenarios[1]['guard_callbacks']['closures']==0
    assert not (exported(scenarios,'guard_callbacks')/'executions.csv').exists()


@pytest.mark.parametrize('name',['invalid_quantity','invalid_quantity_max','invalid_windows','invalid_date','invalid_feed','invalid_nan',
    'invalid_currency','invalid_capital','invalid_leverage','invalid_existing_orders','calendar_missing'])
def test_invalid_configuration_never_creates_an_order_or_export(scenarios,name):
    value=scenarios[1][name]
    assert value['rejected'] and value['submissions']==value['file_queries']==0


def test_causal_crosses_million_unit_conversion_confirmations_and_open_position(scenarios):
    folder=exported(scenarios,'cross');values=scenarios[1]['cross']
    assert values['submissions']==2 and values['closures']==1
    signals=rows(folder,'daily.csv')
    assert [r['signal'] for r in signals]==['none','none','none','enter_long','none','exit_long','enter_long','none']
    executions=rows(folder,'executions.csv')
    assert [r['side'] for r in executions]==['buy','sell','buy']
    assert [r['executed_at'] for r in executions]==['2025-01-05T00:00:00Z','2025-01-07T00:00:00Z','2025-01-08T00:00:00Z']
    assert all(Decimal(r['quantity'])==1000 for r in executions)
    assert all(r['fee']==r['external_id']=='' for r in executions)
    totals=rows(folder,'orders.csv')
    assert [r['state'] for r in totals]==['CLOSED','FILLED'] and Decimal(totals[1]['remaining_amount_millions'])==Decimal('0.001')
    assert all(Decimal(r['aggregate_commission_usd'])>0 for r in totals)
    meta=json.loads((folder/'metadata.json').read_bytes())
    assert meta['strategy_window_end_observed'] and not meta['external_equivalence_verified'] and not meta['native_final_report_reconciled']


def test_partial_fills_and_closes_stay_separate_and_keep_unknown_fees(scenarios):
    executions=rows(exported(scenarios,'partial'),'executions.csv')
    assert len(executions)==6
    assert [Decimal(r['quantity']) for r in executions]==[400,600,300,700,400,600]
    assert all(r['fee']=='' and r['native_order_id'] for r in executions)


def test_a_native_partial_close_is_not_given_a_later_strategy_signal(scenarios):
    folder=exported(scenarios,'earlier_native_close')
    executions=rows(folder,'executions.csv');earlier=executions[1];requested=executions[2]
    assert earlier['side']=='sell' and earlier['quantity']=='400' and earlier['signal_at']=='' and earlier['signal_binding']=='unknown'
    assert requested['side']=='sell' and requested['quantity']=='600' and requested['signal_at']=='2025-01-07T00:00:00Z'
    event=next(r for r in rows(folder,'events.csv') if r['type']=='close_request_not_fill')
    assert event['quantity_eur']=='600'


@pytest.mark.parametrize('name',['out_of_order','crossed','bad_price','hourly_duplicate','hourly_nan','foreign','pending','rejected','history_missing','mutated_parameters','calendar_failure','native_rejection_message'])
def test_failures_are_visible_and_no_retry_is_invented(scenarios,name):
    value=scenarios[1][name];folder=exported(scenarios,name)
    assert value['rejected']
    meta=json.loads((folder/'metadata.json').read_bytes())
    assert meta['has_failure'] and meta['status']=='failed_review_partial_exports'
    assert not meta['external_equivalence_verified']
    if name in ('pending','rejected','native_rejection_message'):assert value['submissions']==1 and value['closures']==0
    if name=='mutated_parameters':assert meta['quantity_eur']=='1000' and value['submissions']==0
    if name=='calendar_failure':assert value['submissions']==0
    if name=='native_rejection_message':
        event=next(r for r in rows(folder,'events.csv') if r['type']=='ORDER_SUBMIT_REJECTED')
        assert event['native_content']=='System offline'
        assert 'System offline' in (folder/'failure.txt').read_text(encoding='utf-8')


def test_native_calendar_skips_closed_interpolation_ticks_and_preserves_friday_signal(scenarios):
    folder=exported(scenarios,'offline_gap')
    daily=rows(folder,'daily.csv')
    assert [r['date'] for r in daily]==['2025-01-06','2025-01-07','2025-01-08','2025-01-09','2025-01-10','2025-01-12']
    assert [r['bid_close'] for r in daily]==['1','1','1','1','2','2.5']
    assert daily[4]['signal']=='enter_long'
    assert daily[4]['fast']=='1.5' and Decimal(daily[4]['slow'])==Decimal('1.333333333333333333333333333')
    execution,=rows(folder,'executions.csv')
    assert execution['executed_at']=='2025-01-12T22:00:00Z' and execution['signal_at']=='2025-01-11T00:00:00Z'
    assert execution['price']=='2.5002' and execution['quantity']=='1000' and execution['fee']==''
    interval,=rows(folder,'calendar.csv')
    assert interval['skipped_ticks']=='4' and interval['first_skipped_tick_at']=='2025-01-10T23:00:00Z'
    assert interval['last_skipped_tick_at']=='2025-01-12T21:59:59.999Z'
    meta=json.loads((folder/'metadata.json').read_bytes())
    assert meta['offline_ticks_skipped']==4 and meta['ticks_processed']==12 and not meta['has_failure']
    assert meta['protocol']=='tiresias_jforex_test_export_v2' and not meta['external_equivalence_verified']


def test_offline_end_boundary_confirms_last_session_without_creating_a_weekend_order(scenarios):
    folder=exported(scenarios,'offline_final_boundary')
    daily=rows(folder,'daily.csv')
    assert len(daily)==5 and daily[-1]['date']=='2025-01-10' and daily[-1]['boundary_observed']=='true'
    assert not rows(folder,'executions.csv') and not rows(folder,'events.csv')
    meta=json.loads((folder/'metadata.json').read_bytes())
    assert meta['strategy_window_end_observed'] and meta['offline_ticks_skipped']==1 and not meta['has_failure']
    assert rows(folder,'calendar.csv')[0]['skipped_ticks']=='1'


def test_unfinished_final_session_does_not_claim_a_confirmed_signal(scenarios):
    folder=exported(scenarios,'unfinished')
    final=rows(folder,'daily.csv')[-1]
    assert final['signal']=='unconfirmed_last_session' and final['boundary_observed']=='false'
    assert not json.loads((folder/'metadata.json').read_bytes())['strategy_window_end_observed']


def test_hourly_native_sides_are_exported_for_later_price_validation(scenarios):
    values=rows(exported(scenarios,'hourly'),'hourly.csv')
    assert len(values)==1 and values[0]['bid_close']=='1' and values[0]['ask_close']=='1.0002'


def test_repeated_stop_does_not_rewrite_or_force_close(scenarios):
    assert scenarios[1]['stop_twice']['closures']==1
    assert len(rows(exported(scenarios,'stop_twice'),'executions.csv'))==3


def test_java_sma_and_requests_match_python_on_the_same_synthetic_utc_sessions(compiled,tmp_path):
    prices=[Decimal('1.10000')+Decimal(i%17-8)*Decimal('0.00001') for i in range(160)]
    start=datetime(2025,1,1,tzinfo=UTC);quotes=tmp_path/'quotes.csv'
    with quotes.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['at','bid','ask'])
        for i,price in enumerate(prices):
            for offset in (0,86399999):
                writer.writerow([int((start+timedelta(days=i)).timestamp()*1000)+offset,str(price),str(price+Decimal('0.0002'))])
        writer.writerow([int((start+timedelta(days=len(prices))).timestamp()*1000),'1.1','1.1002'])
    result=subprocess.run([compiled[0],'-cp',compiled[1],'JForexHarness','replay',str(tmp_path/'replay'),str(quotes),'20','60',
        start.date().isoformat(),(start+timedelta(days=len(prices))).date().isoformat()],cwd=ROOT,check=True,capture_output=True,text=True,timeout=40)
    assert not json.loads(result.stdout)['rejected']
    folder=next((tmp_path/'replay').glob('tiresias-test-*'));daily=rows(folder,'daily.csv')
    quick=simple_moving_average(prices,20);gradual=simple_moving_average(prices,60)
    signals=moving_average_crossover_signals(quick,gradual)
    assert [r['signal'] for r in daily]==[signal.value for signal in signals]
    for row,fast,slow in zip(daily,quick,gradual):
        assert (None if not row['fast'] else Decimal(row['fast']))==fast
        assert (None if not row['slow'] else Decimal(row['slow']))==slow
    requests=[row for row in rows(folder,'events.csv') if row['type'].endswith('_not_fill')]
    expected=[];position=False
    for i,signal in enumerate(signals[:-1]):
        if signal.value=='enter_long' and not position:expected.append(('buy_request_not_fill',i+1));position=True
        elif signal.value=='exit_long' and position:expected.append(('close_request_not_fill',i+1));position=False
    assert [(r['type'],datetime.fromisoformat(r['at'].replace('Z','+00:00')).date()) for r in requests]==[
        (kind,(start+timedelta(days=index)).date()) for kind,index in expected]

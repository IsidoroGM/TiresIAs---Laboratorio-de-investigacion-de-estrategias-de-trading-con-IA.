"""Synthetic native-shaped bundles: parser/accounting QA, never broker evidence."""
import base64
from copy import deepcopy
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import io
import json
import threading
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.jforex_reconciliation import JForexReconciliations, NativeHTML, reconcile, unpack
from trading_ai.tv_contracts import canonical
from test_conversation_prices import make_prices


def csv_bytes(columns, rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def pack(files):
    stream=io.BytesIO()
    with ZipFile(stream,'w',compression=ZIP_DEFLATED) as archive:
        for name,raw in files.items():archive.writestr(name,raw)
    return stream.getvalue()


def html_time(value):return datetime.fromisoformat(value.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M:%S')


@pytest.fixture(scope='module')
def sample(tmp_path_factory):
    root=tmp_path_factory.mktemp('jforex-reference');make_prices(root,days=180)
    service=DukascopyResearch(root);run=service.run(dataset='sample',capital='1000000',quantity='1000',commission_rate='0.001')['id']
    value=service.get(run);daily=json.loads((root/'.local/dukascopy-research'/run/'input-daily.json').read_text(encoding='utf-8'))
    meta={'protocol':'tiresias_jforex_test_export_v2','strategy_revision':'sma_utc_test_v2_native_calendar','engine_type':'TEST',
        'pair':'EUR/USD','currency':'USD','strategy':'sma','fast':20,'slow':60,'quantity_eur':'1000','expected_initial_capital_usd':'1000000',
        'start_date':value['source']['start_date'],'end_date_exclusive':value['source']['end_date_exclusive'],
        'declared_feed':'candles_h1_4ohlc_bid','has_failure':False,'strategy_window_end_observed':True}
    native_days=[];hours=[]
    for day,observation in zip(daily['sessions'],value['observations'],strict=True):
        prices={side+'_'+key:day[side][key] for side in ('bid','ask') for key in ('open','high','low','close')}
        hours.append({'open_at':day['first_observed_open_at'],**prices})
        native_days.append({'date':day['date'],'fast':observation['fast'] or '', 'slow':observation['slow'] or '',
            'signal':observation['signal'],'boundary_observed':'true',**prices})
    executions=[];orders=[];positions=[];current=None
    for fill in value['hypothetical_fills']:
        at=(datetime.fromisoformat(fill['executed_at'].replace('Z','+00:00'))+timedelta(seconds=450)).isoformat().replace('+00:00','Z')
        if fill['side']=='buy':
            current={'native_order_id':str(len(orders)+1),'label':'Synthetic_'+str(len(orders)+1),'state':'FILLED','aggregate_commission_usd':'0.02'}
            orders.append(current);positions.append({'order':current,'entry':at,'entry_price':fill['price']})
        else:
            current['state']='CLOSED';current['aggregate_commission_usd']='0.03';positions[-1].update(exit=at,exit_price=fill['price'])
        executions.append({'external_id':'','executed_at':at,'side':fill['side'],'quantity':fill['quantity'],'price':fill['price'],
            'fee':'','signal_at':fill['signal_at'],'native_order_id':current['native_order_id']})
    assert len(executions)>=3
    params={'startDate':meta['start_date'],'endDateExclusive':meta['end_date_exclusive'],'fast':'20','slow':'60','quantityEur':'1000',
            'expectedCapitalUsd':'1000000.0','declaredFeed':meta['declared_feed']}
    fee=sum(Decimal(r['aggregate_commission_usd']) for r in orders)+Decimal('0.01')
    pairs={'Account Currency':'USD','Initial Equity':'1\u2019000\u2019000','Final Equity':'999\u2019990.00','Commission Fees':str(fee),
        'Last tick time':meta['end_date_exclusive']+' 23:52:30',**params}
    html='<table>'+''.join('<tr><td>'+key+'</td><td>'+val+'</td></tr>' for key,val in pairs.items())+'</table><table>'
    for position in positions:
        data=[position['order']['label'],'0.001','BUY',position['entry_price']]
        if 'exit' in position:data += [position['exit_price'],'-1','-10',html_time(position['entry']),html_time(position['exit']),'']
        else:data += ['1','10',html_time(position['entry']),'']
        html+='<tr>'+''.join('<td>'+val+'</td>' for val in data)+'</tr>'
    first=executions[0];swap_at=(datetime.fromisoformat(first['executed_at'].replace('Z','+00:00'))+timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    html+='<tr><td>'+swap_at+'</td><td>Overnights</td><td>Overnight swap [-1.0] points applied to position ['+positions[0]['order']['label']+', EUR/USD, BUY, 1000.0]</td></tr>'
    html+='<tr><td>'+swap_at+'</td><td>Commission Fees</td><td>Commission Fees ['+str(fee)+']</td></tr></table>'
    files={'report.html':html.encode('utf-8'),'metadata.json':canonical(meta),
        'hourly.csv':csv_bytes(list(hours[0]),hours),'daily.csv':csv_bytes(list(native_days[0]),native_days),
        'calendar.csv':csv_bytes(['first_skipped_tick_at','last_skipped_tick_at','skipped_ticks'],[]),
        'events.csv':csv_bytes(['type','at'],[]),'executions.csv':csv_bytes(list(executions[0]),executions),
        'orders.csv':csv_bytes(list(orders[0]),orders)}
    return root,run,value,files


def test_same_cutoff_gross_swaps_and_fee_scenarios_do_not_invent_native_equity(sample):
    _,_,reference,files=sample;result=reconcile(reference,files,html_timezone='UTC')
    cut=result['common_cutoff']
    assert result['coverage']['matches_reference_sessions'] and not result['coverage']['daily_signal_differences']
    assert cut['derived_swaps_before_cutoff_usd']=='-0.1' and cut['native_equity_observed'] is None
    assert len(cut['diagnostic_scenarios'])==2 and all(not r['native_observation'] for r in cut['diagnostic_scenarios'])
    assert result['commissions']['allocated_to_fills'] is False and 'commission_totals_differ' in result['issues']
    for pair in result['comparison']['pairs']:
        assert pair['differences'][0]['external_minus_python_seconds']==450 and pair['unknown_fields']==['fee']
    assert result['status']=='partial_reconciliation' and not result['external_equivalence_verified']


def test_swaps_after_cutoff_are_separate_and_never_double_count_position_pnl(sample):
    _,_,reference,source=sample;files=dict(source)
    html=files['report.html'].decode().replace('Overnight swap [-1.0]','Overnight swap [-900.0]')
    files['report.html']=html.encode()
    value=reconcile(reference,files,html_timezone='UTC')
    assert value['common_cutoff']['derived_swaps_before_cutoff_usd']=='-90'
    assert value['native_report']['net_change_usd']=='-10' # Reported total is preserved, not recomputed from rounded P/L.
    files['report.html']=html.replace('EUR/USD, BUY, 1000.0','EUR/USD, BUY, 2000.0').encode()
    with pytest.raises(ValueError,match='Cantidad del swap'):reconcile(reference,files,html_timezone='UTC')


def test_a_post_cutoff_swap_does_not_enter_the_common_cutoff_result(sample):
    _,_,reference,source=sample;files=dict(source)
    orders=list(csv.DictReader(io.StringIO(files['orders.csv'].decode())))
    open_order=next((r for r in orders if r['state']=='FILLED'),None)
    if open_order is None:
        at=reference['source']['end_date_exclusive']+'T00:00:00Z'
        entry=(datetime.fromisoformat(at.replace('Z','+00:00'))-timedelta(hours=1)).isoformat().replace('+00:00','Z')
        open_order={'native_order_id':'999','label':'Synthetic_extra_open','state':'FILLED','aggregate_commission_usd':'0.02'}
        orders.append(open_order);files['orders.csv']=csv_bytes(list(orders[0]),orders)
        fills=list(csv.DictReader(io.StringIO(files['executions.csv'].decode())))
        fills.append({**fills[0],'native_order_id':'999','executed_at':entry,'side':'buy','price':'1','signal_at':entry})
        files['executions.csv']=csv_bytes(list(fills[0]),fills)
        files['report.html']+=('<tr>'+''.join('<td>'+v+'</td>' for v in ['Synthetic_extra_open','0.001','BUY','1','0','0',html_time(entry),''])+'</tr>').encode()
    event=reference['source']['end_date_exclusive']+' 22:00:00'
    files['report.html']+=('<tr><td>'+event+'</td><td>Overnights</td><td>Overnight swap [-2.0] points applied to position ['+open_order['label']+', EUR/USD, BUY, 1000.0]</td></tr>').encode()
    result=reconcile(reference,files,html_timezone='UTC')
    assert result['common_cutoff']['derived_swaps_before_cutoff_usd']=='-0.1'
    assert result['common_cutoff']['derived_swaps_after_cutoff_usd']=='-0.2'
    assert 'swaps_after_strategy_cutoff' in result['issues']


def with_snapshots(sample):
    files=dict(sample[3]);meta=json.loads(files['metadata.json']);meta['protocol']='tiresias_jforex_test_export_v3';files['metadata.json']=canonical(meta)
    cutoff=meta['end_date_exclusive']+'T00:00:00Z'
    after=(datetime.fromisoformat(cutoff.replace('Z','+00:00'))+timedelta(seconds=450)).isoformat().replace('+00:00','Z')
    account=[{'reason':'strategy_cutoff','observed_at':after,'target_cutoff_at':cutoff,'currency':'USD','api_equity':'999989.14',
        'api_base_equity':'999986','api_balance_eod':'999999','api_values_may_lag':'true','quote_at':after,'bid':'1.1','ask':'1.1002'}]
    fills=list(csv.DictReader(io.StringIO(files['executions.csv'].decode())))
    snapshots=[]
    for order in csv.DictReader(io.StringIO(files['orders.csv'].decode())):
        net=sum(Decimal(f['quantity'])*(1 if f['side']=='buy' else -1) for f in fills if f['native_order_id']==order['native_order_id'])
        snapshots.append({'reason':'strategy_cutoff','observed_at':after,'target_cutoff_at':cutoff,'native_order_id':order['native_order_id'],
            'state':order['state'],'native_amount_millions':'0.001','open_quantity_eur_from_history':str(net),
            'aggregate_commission_usd':order['aggregate_commission_usd'],'adjusted_open_price':'1.1','native_profit_loss_usd':'-1'})
    files['account-snapshots.csv']=csv_bytes(list(account[0]),account)
    files['order-snapshots.csv']=csv_bytes(list(snapshots[0]),snapshots)
    return files


def with_open_snapshots(sample):
    files=dict(sample[3]);orders=list(csv.DictReader(io.StringIO(files['orders.csv'].decode())))
    if not any(row['state']=='FILLED' for row in orders):
        cutoff=sample[2]['source']['end_date_exclusive']+'T00:00:00Z'
        at=(datetime.fromisoformat(cutoff.replace('Z','+00:00'))-timedelta(hours=1)).isoformat().replace('+00:00','Z')
        orders.append({'native_order_id':'999','label':'Synthetic_open','state':'FILLED','aggregate_commission_usd':'0.02'})
        files['orders.csv']=csv_bytes(list(orders[0]),orders)
        fills=list(csv.DictReader(io.StringIO(files['executions.csv'].decode())))
        fills.append({**fills[0],'native_order_id':'999','executed_at':at,'side':'buy','price':'1','signal_at':at})
        files['executions.csv']=csv_bytes(list(fills[0]),fills)
        files['report.html']+=('<tr>'+''.join('<td>'+v+'</td>' for v in ['Synthetic_open','0.001','BUY','1','0','0',html_time(at),''])+'</tr>').encode()
    return with_snapshots((*sample[:3],files))


def test_v3_observation_is_not_moved_back_to_the_requested_cutoff_or_called_cash(sample):
    value=reconcile(sample[2],with_snapshots(sample),html_timezone='UTC')
    observed=value['common_cutoff']['native_equity_observed']
    assert observed['observed_after_target_seconds']==450 and not observed['exact_cutoff_observation']
    assert observed['api_balance_eod']=='999999' and observed['account_values_may_lag']
    assert 'native_cutoff_snapshot_after_target' in value['issues'] and not value['native_final_report_reconciled']


def test_v3_snapshot_reconstruction_uses_its_quote_and_keeps_api_residuals(sample):
    files=with_open_snapshots(sample);value=reconcile(sample[2],files,html_timezone='UTC')
    snapshot=value['snapshot_valuations'][0]
    assert snapshot['open_quantity_eur']=='1000'
    assert snapshot['api_net_change_usd']=='-10.86' and snapshot['api_equity_usd']=='999989.14'
    assert snapshot['observed_at']==value['common_cutoff']['native_equity_observed']['observed_at']
    assert snapshot['bid']=='1.1' and not snapshot['synchronized_equity_verified']
    assert snapshot['matches_html_final_equity'] is None
    assert snapshot['account_values_may_lag'] and snapshot['scenarios_are_not_certified_bounds']
    for scenario in snapshot['diagnostic_scenarios']:
        assert Decimal(scenario['reconstructed_equity_usd'])+Decimal(scenario['api_minus_reconstructed_usd'])==Decimal('999989.14')
        assert not scenario['native_observation']
    accounts=list(csv.DictReader(io.StringIO(files['account-snapshots.csv'].decode())))
    accounts[0]['bid']='1.1001';files['account-snapshots.csv']=csv_bytes(list(accounts[0]),accounts)
    changed=reconcile(sample[2],files,html_timezone='UTC')
    assert changed['common_cutoff']['gross_equity_from_fills_usd']==value['common_cutoff']['gross_equity_from_fills_usd']
    assert Decimal(changed['snapshot_valuations'][0]['gross_equity_from_fills_usd'])-Decimal(snapshot['gross_equity_from_fills_usd'])==Decimal(snapshot['open_quantity_eur'])*Decimal('0.0001')


def test_v3_fee_event_after_cutoff_is_only_used_in_snapshots_after_its_date(sample):
    files=with_snapshots(sample);before=reconcile(sample[2],files,html_timezone='UTC')
    at=before['snapshot_valuations'][0]['observed_at']
    # At the snapshot, one published event is known. The later event is preserved but not charged early.
    later=(datetime.fromisoformat(at.replace('Z','+00:00'))+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
    for date,fee in [(html_time(at),'0.17'),(later,'3.00')]:
        files['report.html']+=('<tr><td>'+date+'</td><td>Commission Fees</td><td>Commission Fees ['+fee+']</td></tr>').encode()
    value=reconcile(sample[2],files,html_timezone='UTC')
    old=before['snapshot_valuations'][0]['diagnostic_scenarios'];new=value['snapshot_valuations'][0]['diagnostic_scenarios']
    assert Decimal(new[0]['commission_usd'])-Decimal(old[0]['commission_usd'])==Decimal('0.17')
    assert Decimal(old[0]['reconstructed_equity_usd'])-Decimal(new[0]['reconstructed_equity_usd'])==Decimal('0.17')
    assert new[1]==old[1] # Order aggregates are an independent scenario, not added to event fees.
    assert value['common_cutoff']['diagnostic_scenarios']==[]


def test_v3_snapshot_includes_post_cutoff_swaps_only_when_observed_by_its_date(sample):
    files=with_open_snapshots(sample);before=reconcile(sample[2],files,html_timezone='UTC')
    at=before['snapshot_valuations'][0]['observed_at']
    orders=list(csv.DictReader(io.StringIO(files['orders.csv'].decode())))
    label=next(row['label'] for row in orders if row['state']=='FILLED')
    later=(datetime.fromisoformat(at.replace('Z','+00:00'))+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
    for date,points in [(html_time(at),'-2'),(later,'-900')]:
        files['report.html']+=('<tr><td>'+date+'</td><td>Overnights</td><td>Overnight swap ['+points+'] points applied to position ['+label+', EUR/USD, BUY, 1000.0]</td></tr>').encode()
    value=reconcile(sample[2],files,html_timezone='UTC')
    assert Decimal(value['snapshot_valuations'][0]['derived_swaps_to_observation_usd'])-Decimal(before['snapshot_valuations'][0]['derived_swaps_to_observation_usd'])==Decimal('-0.2')
    assert value['common_cutoff']['derived_swaps_before_cutoff_usd']==before['common_cutoff']['derived_swaps_before_cutoff_usd']
    assert value['common_cutoff']['derived_swaps_after_cutoff_usd']=='-90.2'


def test_v3_tester_stop_preserves_observation_and_compares_html_without_certifying_equivalence(sample):
    files=with_snapshots(sample)
    accounts=list(csv.DictReader(io.StringIO(files['account-snapshots.csv'].decode())))
    stop={**accounts[0],'reason':'tester_stop','observed_at':sample[2]['source']['end_date_exclusive']+'T23:52:30Z','api_equity':'999990'}
    stop['quote_at']=stop['observed_at'];accounts.append(stop)
    files['account-snapshots.csv']=csv_bytes(list(accounts[0]),accounts)
    orders=list(csv.DictReader(io.StringIO(files['order-snapshots.csv'].decode())))
    orders.extend({**row,'reason':'tester_stop','observed_at':stop['observed_at']} for row in list(orders))
    files['order-snapshots.csv']=csv_bytes(list(orders[0]),orders)
    value=reconcile(sample[2],files,html_timezone='UTC');final=value['snapshot_valuations'][-1]
    assert final['matches_html_final_equity'] and final['api_net_change_usd']=='-10'
    assert not value['native_final_report_reconciled'] and not value['external_equivalence_verified']
    accounts[-1]['api_equity']='999990.01';files['account-snapshots.csv']=csv_bytes(list(accounts[0]),accounts)
    assert not reconcile(sample[2],files,html_timezone='UTC')['snapshot_valuations'][-1]['matches_html_final_equity']


@pytest.mark.parametrize('change',['missing','wrong_cutoff','early','invented_exposure','unknown_order','unreported_lag'])
def test_v3_mixed_or_misleading_snapshots_are_rejected(sample,change):
    files=with_snapshots(sample)
    if change=='missing':del files['account-snapshots.csv']
    elif change=='wrong_cutoff':files['account-snapshots.csv']=files['account-snapshots.csv'].replace(b'T00:00:00Z',b'T01:00:00Z')
    elif change=='early':
        records=list(csv.DictReader(io.StringIO(files['account-snapshots.csv'].decode())))
        before=(datetime.fromisoformat(records[0]['target_cutoff_at'].replace('Z','+00:00'))-timedelta(minutes=1)).isoformat().replace('+00:00','Z')
        records[0]['observed_at']=records[0]['quote_at']=before
        files['account-snapshots.csv']=csv_bytes(list(records[0]),records)
    elif change=='invented_exposure':files['order-snapshots.csv']=files['order-snapshots.csv'].replace(b',0,',b',1000,',1)
    elif change=='unknown_order':files['order-snapshots.csv']=files['order-snapshots.csv'].replace(b',1,CLOSED',b',999,CLOSED',1)
    else:files['account-snapshots.csv']=files['account-snapshots.csv'].replace(b',true,',b',false,')
    with pytest.raises(ValueError):reconcile(sample[2],files,html_timezone='UTC')


@pytest.mark.parametrize('field,value',[('engine_type','LIVE'),('currency','EUR'),('has_failure',True),('strategy_window_end_observed',False),('declared_feed','ticks_all'),('protocol','unknown')])
def test_incompatible_or_incomplete_native_runs_are_blocked(sample,field,value):
    _,_,reference,source=sample;files=dict(source);meta=json.loads(files['metadata.json']);meta[field]=value;files['metadata.json']=canonical(meta)
    with pytest.raises(ValueError):reconcile(reference,files,html_timezone='UTC')


@pytest.mark.parametrize('zone',['Europe/Madrid','EET','guess',None])
def test_html_zone_is_explicit_and_not_guessed(sample,zone):
    with pytest.raises(ValueError,match='UTC'):reconcile(sample[2],sample[3],html_timezone=zone)


@pytest.mark.parametrize('change',['capital','parameter','duplicate_summary','exception','bad_date','wrong_quantity','missing_position','duplicate_h1','invalid_ohlc','bad_calendar','daily_mismatch','duplicate_order','orphan_fill'])
def test_mixed_or_tampered_native_bundle_is_rejected(sample,change):
    _,_,reference,source=sample;files=dict(source)
    if change=='capital':files['report.html']=files['report.html'].replace('1\u2019000\u2019000'.encode(),b'100000')
    elif change=='parameter':files['report.html']=files['report.html'].replace(b'<td>fast</td><td>20',b'<td>fast</td><td>21')
    elif change=='duplicate_summary':files['report.html']+=b'<tr><td>Account Currency</td><td>USD</td></tr>'
    elif change=='exception':files['report.html']+=b'<tr><td>2025-01-01 00:00:00</td><td>Exception</td><td>failure</td></tr>'
    elif change=='bad_date':files['report.html']=files['report.html'].replace(b'00:07:30',b'01:07:30')
    elif change=='wrong_quantity':files['report.html']=files['report.html'].replace(b'<td>0.001</td>',b'<td>0.002</td>')
    elif change=='missing_position':files['report.html']=files['report.html'].replace(b'Synthetic_1',b'Unknown_1')
    elif change=='duplicate_h1':files['hourly.csv']+=files['hourly.csv'].splitlines()[-1]+b'\n'
    elif change=='invalid_ohlc':files['hourly.csv']=files['hourly.csv'].replace(b'1.0225',b'0',1)
    elif change=='bad_calendar':files['calendar.csv']+=b'2025-01-01T00:00:00Z,2025-01-01T00:52:30Z,4\n'
    elif change=='daily_mismatch':files['daily.csv']=files['daily.csv'].replace(b'1.0225',b'1.2225',1)
    elif change=='duplicate_order':files['orders.csv']+=files['orders.csv'].splitlines()[-1]+b'\n'
    else:files['executions.csv']=files['executions.csv'].replace(b',1\r\n',b',999\r\n',1)
    with pytest.raises(ValueError):reconcile(reference,files,html_timezone='UTC')


@pytest.mark.parametrize('change',['missing','traversal','duplicate','oversize','not_zip'])
def test_zip_is_bounded_and_never_extracts_paths(sample,change):
    files=dict(sample[3])
    if change=='missing':del files['metadata.json']
    elif change=='traversal':files['../outside']=b'x'
    elif change=='oversize':files['report.html']=b'x'*(2*1024*1024+1)
    raw=pack(files)
    if change=='duplicate':
        stream=io.BytesIO(raw)
        with pytest.warns(UserWarning,match='Duplicate name'):
            with ZipFile(stream,'a') as z:z.writestr('report.html',b'x')
        raw=stream.getvalue()
    if change=='not_zip':raw=b'not a ZIP'
    with pytest.raises(ValueError):unpack(raw)


def test_scripts_are_ignored_not_executed_or_used_as_report_cells():
    parser=NativeHTML(b'<script><tr><td>Account Currency</td><td>EUR</td></tr></script><tr><td>Account Currency</td><td>USD</td></tr>')
    assert parser.value('Account Currency')=='USD'


def test_reference_scale_must_match_before_presenting_common_cutoff(sample):
    reference=deepcopy(sample[2]);reference['configuration']['initial_capital']='1000'
    with pytest.raises(ValueError,match='mismo'):reconcile(reference,sample[3],html_timezone='UTC')


def test_preview_save_idempotence_hashes_and_read_only_get(sample,tmp_path,monkeypatch):
    import shutil
    root,run,_,files=sample;target=tmp_path/'.local/dukascopy-research'/run
    shutil.copytree(root/'.local/dukascopy-research'/run,target)
    repo=JForexReconciliations(tmp_path);values={'run':run,'raw':pack(files),'name':'synthetic-native.zip','html_timezone':'UTC'}
    def forbidden(*a,**kw):raise AssertionError('No model, strategy run, or account action is allowed')
    monkeypatch.setattr(DukascopyResearch,'run',forbidden)
    preview=repo.preview(**values);assert not repo.directory.exists()
    with pytest.raises(ValueError):repo.save(approval_sha256='0'*64,**values)
    saved=repo.save(approval_sha256=preview['approval_sha256'],**values)
    assert saved['created'] and repo.get(saved['id'])==preview['preview']
    assert not repo.save(approval_sha256=preview['approval_sha256'],**values)['created']
    monkeypatch.setattr('trading_ai.jforex_reconciliation.reconcile',forbidden)
    assert repo.overview()['metadata_only'] and repo.get(saved['id'])==preview['preview']
    (repo.directory/saved['id']/'original.zip').write_bytes(b'changed')
    with pytest.raises(ValueError):repo.get(saved['id'])
    assert not (tmp_path/'.local/simulation').exists()


def test_http_guards_and_native_preview_have_no_account_or_model_effects(sample):
    from trading_ai.lab import create_server
    from test_conversation import request,auth
    root,run,_,files=sample;server=create_server(root=root,port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        body={'action':'preview_jforex_reconciliation','run':run,'name':'synthetic-native.zip','zip_base64':base64.b64encode(pack(files)).decode(),'html_timezone':'UTC'}
        assert request(server,'/api/simulation','POST',json.dumps(body))[0]==403
        headers=auth(server);status,preview=request(server,'/api/simulation','POST',json.dumps(body),**headers)
        assert status==202 and preview['preview']['status']=='partial_reconciliation'
        status,saved=request(server,'/api/simulation','POST',json.dumps({**body,'action':'save_jforex_reconciliation','approve_preview_sha256':preview['approval_sha256']}),**headers)
        assert status==202
        assert request(server,'/api/simulation/jforex-reconciliations/'+saved['id'])[1]==preview['preview']
        assert request(server,'/api/chat')[1]['reserved']=={'model_requests':0,'experiments':0}
        assert request(server,'/api/simulation')[1]['jforex_reconciliations']['metadata_only']
    finally:server.shutdown();thread.join();server.server_close()

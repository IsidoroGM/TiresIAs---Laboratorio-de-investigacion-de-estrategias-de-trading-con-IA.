"""Contratos y referencia verificables sin cuenta o compilador TradingView."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import localcontext
import json

import pytest

from trading_ai.tv_contracts import checksum, instant, make_contract, milliseconds, number, validate_contract, validate_fill
from trading_ai.tv_pine import alert_template, render, verify_bundle, write_bundle
from trading_ai.tv_reference import compare_observations, read_bars_csv, run_reference, validate_bars


def contract(**changes):
    return make_contract(**dict(fast=2,slow=3,ticker="SYNTH:EURUSD",start="2020-01-01T00:00:00Z",end="2021-01-01T00:00:00Z",capital="100",cost_rate="0.01") | changes)


def bars(prices=(3,2,1,2,3,2,1,2)):
    result=[]
    for i,price in enumerate(prices):
        day=datetime(2020,1,1,tzinfo=UTC)+timedelta(days=i)
        opening=9 if i==5 else 11 if i==7 else price
        result.append({'open_at':day.isoformat(),'close_at':(day+timedelta(hours=23)).isoformat(),
                       'open':str(opening),'high':str(max(opening,price)),'low':str(min(opening,price)),'close':str(price)})
    return result


def test_contract_identity_is_canonical_and_allocation_is_fixed():
    c=contract();alias=deepcopy(c);alias['account']['initial_capital']='100.00'
    assert checksum(validate_contract(alias))==checksum(c)
    assert c['execution']['fill']=='next_bar_open'
    assert c['execution']['sizing']=='fixed_base_units'
    assert c['market']['ticker']=='SYNTH:EURUSD'


@pytest.mark.parametrize('group,key,value',[
    ('strategy','kind','short'),('strategy','fast',True),('strategy','slow',2),
    ('market','ticker','X:USD"\nstrategy.entry("bad")'),('market','timeframe','5'),('market','chart','heikin_ashi'),
    ('market','quote_currency','JPY'),('account','currency','EUR'),('account','initial_capital','NaN'),
    ('account','quantity','-1'),('account','cost_rate','0.2'),('account','id','../../secret'),
    ('execution','pyramiding',False),('period','start','2020-01-01'),('period','end','2050-01-01T00:00:00Z')])
def test_invalid_contract_rejected(group,key,value):
    c=contract();c[group][key]=value
    with pytest.raises((ValueError,TypeError)):validate_contract(c)


def test_zero_exponent_cannot_allocate_huge_memory():
    with pytest.raises(ValueError):number('0e-99999999','value')
    with pytest.raises(ValueError):instant('2020-01-01T00:00:00.000001Z')
    assert milliseconds('1970-01-01T01:00:00.001+01:00')==1


@pytest.mark.parametrize('value',['1_000','١٢','NaN','Infinity','.5','0e-99999999'])
def test_contract_numbers_do_not_accept_ambiguous_or_unbounded_representations(value):
    with pytest.raises(ValueError):number(value,'valor')


def test_negative_zero_and_nanosecond_truncation_cannot_change_contract_identity():
    assert contract(cost_rate='-0')['account']['cost_rate']=='0'
    with pytest.raises(ValueError):instant('2020-01-01T00:00:00.0000001Z')
    from trading_ai.tv_contracts import strict_json
    with pytest.raises(ValueError,match='profundo'):strict_json('['*1500+'0'+']'*1500)


@pytest.mark.parametrize('flag',['pine_compiled','chart_verified','external_connection'])
def test_manifest_cannot_claim_unperformed_external_verification(tmp_path,flag):
    target=tmp_path/'bundle';write_bundle(target,contract())
    value=json.loads((target/'manifest.json').read_text());value[flag]=True
    (target/'manifest.json').write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(ValueError,match='externa'):verify_bundle(target)


@pytest.mark.parametrize('kind',['sma','ema'])
def test_generated_pine_does_not_claim_compilation_and_is_verified(tmp_path,kind):
    c=contract(strategy=kind);text=render(c)
    assert text.startswith('//@version=6\n')
    assert 'process_orders_on_close=false' in text
    assert 'calc_on_every_tick=false' in text
    assert 'ta.ema(' not in text
    assert 'barstate.isconfirmed' in text and 'time_close < END' in text
    assert 'strategy.short' not in text
    assert 'commission_value=1' in text
    assert '{{strategy.order.price}}' in alert_template(c)
    assert '{{strategy.order.contracts}}' in alert_template(c)
    directory=tmp_path/'bundle';manifest=write_bundle(directory,c)
    assert manifest['pine_compiled'] is manifest['chart_verified'] is False
    assert verify_bundle(directory)==c
    (directory/'strategy.pine').write_text(text+'\n// edited',encoding='utf-8')
    with pytest.raises(ValueError,match='alterado'):verify_bundle(directory)


def test_bundle_does_not_overwrite_existing_directory(tmp_path):
    target=tmp_path/'bundle';write_bundle(target,contract())
    with pytest.raises(FileExistsError):write_bundle(target,contract())


def test_decimal_context_does_not_change_contract_or_pine():
    c=contract();expected=render(c)
    with localcontext() as ctx:
        ctx.prec=2
        assert render(c)==expected


def test_reference_fills_next_open_with_gap_and_fees_once():
    result=run_reference(contract(),bars())
    assert [(e['side'],e['price'],e['fee']) for e in result['fills']]==[('buy','9','0.09'),('sell','11','0.11')]
    assert result['summary']['final_equity']=='101.8'
    assert result['summary']['realized_pnl']=='1.8'
    assert result['summary']['total_costs']=='0.2'
    assert result['summary']['closed_trades']==1
    assert result['pine_executed'] is False
    for e in result['fills']:assert validate_fill(e,contract())==e


def test_trailing_signal_remains_pending_without_invented_price():
    result=run_reference(contract(),bars((3,2,1,2,3)))
    assert result['fills']==[]
    assert result['pending_order']['side']=='buy'
    assert 'price' not in result['pending_order']


def test_insufficient_cash_is_rejected_at_future_open():
    c=contract();c['account']['initial_capital']='5'
    result=run_reference(c,bars())
    assert result['fills']==[]
    assert result['rejected_orders'][0]['reason']=='insufficient_cash_at_next_open'
    assert result['summary']['final_equity']=='5'


def test_ema_seed_reset_and_causality():
    c=contract(strategy='ema');values=bars((1,2,3,4,3,2,1))
    result=run_reference(c,values)
    assert result['observations'][1]['fast']=='1.5'
    assert result['observations'][2]['slow']=='2'
    assert result['observations'][3]['slow']=='3'
    assert run_reference(c,values[:4])['observations']==result['observations'][:4]
    with localcontext() as ctx:
        ctx.prec=3
        assert run_reference(c,values)==result


def test_comparison_never_labels_synthetic_data_as_external_verified():
    reference=run_reference(contract(),bars())
    exported=[{key:row[key] for key in ('close_at','fast','slow','signal')} for row in reference['observations']]
    assert compare_observations(reference,exported)['matches']
    assert compare_observations(reference,exported)['external_origin_verified'] is False
    exported[-1]['signal']='enter_long'
    assert not compare_observations(reference,exported)['matches']
    exported[-1]['close_at']='2020-02-01T23:00:00Z'
    with pytest.raises(ValueError,match='Fechas'):compare_observations(reference,exported)


@pytest.mark.parametrize('mode',['duplicate','overlap','bad_high','bad_low','naive','float'])
def test_invalid_ohlc_rejected(mode):
    values=bars()
    if mode=='duplicate':values[1]=deepcopy(values[0])
    if mode=='overlap':values[1]['open_at']=values[0]['open_at']
    if mode=='bad_high':values[0]['high']='0.1'
    if mode=='bad_low':values[0]['low']='99'
    if mode=='naive':values[0]['close_at']='2020-01-01T23:00:00'
    if mode=='float':values[0]['close']=1.2
    with pytest.raises(ValueError):validate_bars(values)


def test_csv_profile_requires_explicit_columns_and_timezone():
    with pytest.raises(ValueError):read_bars_csv(b'time,close\n2020-01-01,2\n')
    raw=b'open_at,close_at,open,high,low,close\n2020-01-01T00:00:00Z,2020-01-01T23:00:00Z,1,2,1,2\n'
    assert read_bars_csv(raw)[0]['close']=='2'

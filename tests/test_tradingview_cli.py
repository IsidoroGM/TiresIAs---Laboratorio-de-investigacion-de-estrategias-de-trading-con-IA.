"""Recorrido público por CLI: referencia, recepción, contabilidad y conciliación."""

import csv
import io
import json

from trading_ai.tradingview import main
from trading_ai.tv_contracts import canonical, checksum, make_contract, strict_json
from trading_ai.tv_reference import run_reference
from trading_ai.tv_simulation import SimulationLedger


def test_cli_prepare_verify_register_and_query(tmp_path,capsys):
    def run(*args):
        assert main(['--root',str(tmp_path),*map(str,args)])==0
        return json.loads(capsys.readouterr().out)
    path=tmp_path/'contract.json'
    run('new-contract','--strategy','ema','--fast','2','--slow','3','--pair','EUR/USD','--ticker','SYNTH:EURUSD',
        '--start','2020-01-01T00:00:00Z','--end','2021-01-01T00:00:00Z','--account','cli-demo','--capital','100',
        '--quantity','1','--cost-rate','0.01','--output',path)
    c=strict_json(path.read_bytes());identity=checksum(c)
    assert run('prepare','--contract',path)['id']==identity
    assert not run('verify','--bundle',identity)['pine_compiled']
    assert run('register','--contract',path)['account']==identity
    assert run('overview')['external_connection'] is False
    assert run('account','--account',identity)['state']['cash']=='100'
    assert run('process','--account',identity)['applied']==[]
    assert run('mark','--account',identity,'--price','2','--at','2020-01-01T00:00:00Z','--mark-id','cli-m1')['duplicate'] is False
    external=tmp_path/'external.json';external.write_bytes(canonical({'as_of':'2020-01-01T00:00:00Z','currency':'USD','cash':'100','quantity':'0','equity':'100'}))
    assert run('reconcile','--account',identity,'--external',external)['matches']


def test_cli_reference_matches_manual_ohlc_and_fills_once(tmp_path,capsys):
    c=make_contract(fast=2,slow=3,ticker='SYNTH:EURUSD',start='2020-01-01T00:00:00Z',end='2021-01-01T00:00:00Z',capital='100',cost_rate='0.01')
    path=tmp_path/'contract.json';path.write_bytes(canonical(c))
    bars=[{'open_at':f'2020-01-{i:02d}T00:00:00Z','close_at':f'2020-01-{i:02d}T23:00:00Z',
           'open':str(p),'high':str(p),'low':str(p),'close':str(p)} for i,p in enumerate([3,2,1,2,3,4],1)]
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(bars[0]));writer.writeheader();writer.writerows(bars)
    source=tmp_path/'bars.csv';source.write_text(stream.getvalue(),encoding='utf-8')
    result=tmp_path/'reference.json'
    assert main(['--root',str(tmp_path),'reference','--contract',str(path),'--bars',str(source),'--output',str(result)])==0
    reference=strict_json(result.read_bytes());assert reference==run_reference(c,bars)
    ledger=SimulationLedger(tmp_path);identity=ledger.register(c)['account']
    event=tmp_path/'fill.json';event.write_bytes(canonical(reference['fills'][0]))
    args=['--root',str(tmp_path),'receive','--file',str(event)]
    assert main(args)==0;assert main(args)==0
    capsys.readouterr()
    assert main(['--root',str(tmp_path),'process','--account',identity])==0
    assert json.loads(capsys.readouterr().out)['applied']==[reference['fills'][0]['execution_id']]
    assert ledger.account(identity)['state']['cash']=='95.96'
    assert main(['--root',str(tmp_path),'reference','--contract',str(path),'--bars',str(source),'--output',str(result)])==2
    assert 'Error:' in capsys.readouterr().err


def test_invalid_config_and_missing_token_fail_without_storage(tmp_path,capsys,monkeypatch):
    path=tmp_path/'invalid.json';path.write_text('{"protocol":"bad"}',encoding='utf-8')
    assert main(['--root',str(tmp_path),'register','--contract',str(path)])==2
    monkeypatch.delenv('TIRESIAS_WEBHOOK_TOKEN',raising=False)
    assert main(['--root',str(tmp_path),'serve','--port','0'])==2
    assert 'token' in capsys.readouterr().err
    assert not (tmp_path/'.local').exists()

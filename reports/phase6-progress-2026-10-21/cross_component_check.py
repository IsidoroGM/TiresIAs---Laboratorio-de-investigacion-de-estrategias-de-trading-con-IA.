"""Contraste artificial de cálculos OHLC y contabilidad; no inicia servicios o IA."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[1]
sys.path.insert(0,str(ROOT))

from trading_ai.tv_contracts import canonical, checksum, make_contract
from trading_ai.tv_reference import run_reference
from trading_ai.tv_simulation import RISK, SimulationLedger


work = ROOT/'.local/phase6-cross-component-20261021'
if work.exists(): raise ValueError('El contraste requiere un espacio nuevo.')
work.mkdir()
ledger = SimulationLedger(work)
cases, observed = [], 0
for seed in range(12):
    rng = random.Random(seed)
    bars = []
    for index in range(70):
        day = datetime(2020,1,1,tzinfo=UTC)+timedelta(days=index)
        opening,closing = [str(Decimal(rng.randrange(100,3001))/100) for _ in range(2)]
        bars.append({'open_at':day.isoformat(),'close_at':(day+timedelta(hours=23)).isoformat(),
                     'open':opening,'close':closing,'high':str(max(Decimal(opening),Decimal(closing))),
                     'low':str(min(Decimal(opening),Decimal(closing)))})
    for kind in ('sma','ema'):
        for fast,slow in ((2,5),(3,8)):
            pair = ('EUR/USD','GBP/USD','USD/JPY','USD/CHF')[seed%4]
            contract = make_contract(strategy=kind,fast=fast,slow=slow,pair=pair,ticker='SYNTH:'+pair.replace('/',''),
                                     start='2020-01-01T00:00:00Z',end='2021-01-01T00:00:00Z',
                                     account=f'artificial-{seed}-{kind}-{fast}-{slow}',capital='1000',quantity='2',cost_rate='0.003')
            reference = run_reference(contract,bars)
            # Para aislar el contraste aritmético, se registra explícitamente un
            # límite de drawdown del 100 %. Las pruebas de pausa por riesgo se
            # verifican por separado en test_tv_simulation.py.
            identity = ledger.register(contract,{**RISK,'max_drawdown_fraction':'1'})['account']
            by_open = {event['executed_at']:event for event in reference['fills']}
            for index,point in enumerate(reference['equity_curve']):
                opening = reference['observations'][index]['open_at']
                if opening in by_open:
                    event = by_open[opening]
                    receipt = ledger.receive(canonical(event))
                    assert receipt['state']=='queued'
                    assert ledger.process(identity)['applied']==[event['execution_id']]
                    if index%3==0:
                        assert ledger.receive(canonical(event))['state']=='duplicate'
                        assert ledger.process(identity)['applied']==[]
                ledger.mark(identity,price=point['price'],at=point['at'],mark_id='artificial-close-'+str(index))
                state = ledger.account(identity,as_of=point['at'])['state']
                for key in ('cash','quantity','equity'):
                    assert state[key]==point[key], (seed,kind,fast,slow,index,key,state[key],point[key])
                observed += 1
            final = ledger.account(identity,as_of=reference['equity_curve'][-1]['at'])
            assert final['state']['fees']==reference['summary']['total_costs']
            assert final['state']['realized_pnl']==reference['summary']['realized_pnl']
            assert not final['state']['risk_paused']
            assert final['state']['rejections']==0
            cases.append({'seed':seed,'strategy':kind,'fast':fast,'slow':slow,'pair':pair,'account':identity,
                          'contract_sha256':checksum(contract),'bars_sha256':sha256(canonical(bars)).hexdigest(),
                          'fill_count':len(reference['fills']),'cash':final['state']['cash'],'quantity':final['state']['quantity'],
                          'equity':final['state']['equity'],'fees':final['state']['fees'],'realized_pnl':final['state']['realized_pnl'],
                          'chain_sha256':final['chain_sha256']})
    print('Semilla artificial completada:',seed,flush=True)

result = {'protocol':'tiresias_phase6_cross_component_check_v1','status':'passed','artificial_data':True,
          'cases':cases,'cases_count':len(cases),'bar_close_states_compared':observed,
          'fields_at_each_close':['cash','quantity','equity'],'fields_at_final_close':['fees','realized_pnl'],
          'python_reference_only':True,'pine_executed':False,'model_requests':0,'external_connection':False,
          'risk_policy':{'max_drawdown_fraction':'1','reason':'isolate_arithmetic_comparison'},
          'drawdown_comparison':False,'drawdown_note':'The ledger also values executions at their opening; the reference drawdown samples closes.',
          'source_sha256':{path.relative_to(ROOT).as_posix():sha256(path.read_bytes()).hexdigest()
                           for path in (Path(__file__),*ROOT.joinpath('trading_ai').glob('tv_*.py'))}}
with (DIRECTORY/'cross-component-result.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps({key:result[key] for key in ('status','cases_count','bar_close_states_compared','pine_executed','external_connection')}))

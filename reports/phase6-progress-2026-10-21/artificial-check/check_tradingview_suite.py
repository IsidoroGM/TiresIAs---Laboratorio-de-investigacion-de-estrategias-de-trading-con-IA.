"""Ensayo artificial reproducible de FASE 6; nunca utiliza datos ni cuentas externas."""

import argparse
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import statistics
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trading_ai.lab import create_server
from trading_ai.tv_contracts import canonical, checksum, make_contract
from trading_ai.tv_io import BundleRepository
from trading_ai.tv_reference import run_reference
from trading_ai.tv_receiver import create_receiver
from trading_ai.tv_simulation import SimulationLedger


class NoModel:
    def complete(self, *_): raise AssertionError("El ensayo no autoriza llamadas al modelo.")


def write(directory, name, value):
    with (directory / name).open("xb") as stream: stream.write(canonical(value) + b"\n")


def inspect_readonly(root, port):
    def files(): return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in root.rglob('*') if path.is_file()}
    before=files();measurements={}
    for route in ('/api/home','/api/experiments','/api/consumption','/api/simulation'):
        samples=[]
        for _ in range(30):
            started=time.perf_counter();connection=HTTPConnection('127.0.0.1',port,timeout=5)
            connection.request('GET',route);response=connection.getresponse();response.read();connection.close()
            assert response.status==200
            samples.append((time.perf_counter()-started)*1000)
        measurements[route]={'samples':len(samples),'p50_ms':statistics.median(samples),'p95_ms':sorted(samples)[28]}
    return {'identical_before_after':before==files(),'files':len(before),'http':measurements}


def check(root, output):
    if root.exists(): raise ValueError("El espacio de ensayo debe ser nuevo, para no mezclar cuentas o evidencias.")
    root.mkdir(parents=True);output.mkdir(parents=True,exist_ok=False)
    c=make_contract(fast=2,slow=3,ticker='SYNTH:EURUSD',start='2020-01-01T00:00:00Z',end='2021-01-01T00:00:00Z',capital='100',cost_rate='0.01')
    bars=[]
    for i,p in enumerate((3,2,1,2,3,2,1,2)):
        day=datetime(2020,1,1,tzinfo=UTC)+timedelta(days=i);opening=9 if i==5 else 11 if i==7 else p
        bars.append({'open_at':day.isoformat(),'close_at':(day+timedelta(hours=23)).isoformat(),
                     'open':str(opening),'high':str(max(opening,p)),'low':str(min(opening,p)),'close':str(p)})
    reference=run_reference(c,bars);identity=checksum(c)
    bundles=BundleRepository(root);bundles.create(c)
    store=SimulationLedger(root);store.register(c)
    server=create_receiver(store,token='artificial-local-test-'+'x'*32,port=0)
    worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.05});worker.start()
    receipts=[]
    try:
        # La salida llega primero: debe esperar a la entrada, incluso tras reinicio.
        for event in (reference['fills'][1],reference['fills'][0],reference['fills'][0]):
            connection=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            connection.request('POST','/events',body=canonical(event),headers={'Authorization':'Bearer '+'artificial-local-test-'+'x'*32,'Content-Type':'application/json'})
            response=connection.getresponse();result=json.loads(response.read());connection.close()
            assert response.status==202 and result['accounting_processed'] is False
            receipts.append(result)
    finally:server.shutdown();worker.join();server.server_close()
    assert store.account(identity)['state']['cash']=='100'
    store=SimulationLedger(root);processed=store.process(identity)
    # El patrimonio final de la referencia usa el cierre final; marcar ese mismo
    # cierre alinea instantes y evita comparar una ejecución con otra cotización.
    final=reference['equity_curve'][-1]
    store.mark(identity,price=final['price'],at=final['at'],mark_id='final-artificial-close')
    account=store.account(identity,as_of=final['at'])
    reconciliation=store.reconcile(identity,{'as_of':final['at'],'currency':'USD','cash':final['cash'],'quantity':final['quantity'],'equity':final['equity']})
    assert reconciliation['matches'] and account['state']['cash']=='101.78'
    assert len(processed['applied'])==2 and receipts[-1]['state']=='duplicate'
    lab=create_server(root=root,port=0,refresh_interval=60,chat_provider=NoModel())
    worker=threading.Thread(target=lab.serve_forever,kwargs={'poll_interval':0.05});worker.start()
    try:reads=inspect_readonly(root,lab.server_port)
    finally:lab.shutdown();worker.join();lab.server_close()
    assert reads['identical_before_after']
    for name,value in (('contract.json',c),('ohlc-artificial.json',bars),('python-reference.json',reference),('receipts.json',receipts),
                       ('processed.json',processed),('virtual-account.json',account),('reconciliation.json',reconciliation),('readonly-http.json',reads)):
        write(output,name,value)
    for name in ('strategy.pine','manifest.json','alert-message.json.txt'):
        (output/name).write_bytes((root/'.local'/'tradingview-bundles'/identity/name).read_bytes())
    # Backup consistente después de cerrar servidores; conserva originales y asientos.
    import sqlite3
    with sqlite3.connect(store.path.as_uri()+'?mode=ro',uri=True) as source:
        with sqlite3.connect(output/'virtual-ledger.sqlite3') as target:source.backup(target)
    evidence={'protocol':'tiresias_phase6_artificial_check_v1','created_at':datetime.now(UTC).isoformat(),
              'artificial_data':True,'external_connection':False,'pine_executed':False,'model_requests':0,
              'files_sha256':{path.name:sha256(path.read_bytes()).hexdigest() for path in output.iterdir() if path.is_file()}}
    write(output,'evidence-manifest.json',evidence)
    return {'account':identity,'final_cash':'101.78','reconciliation_matches':True,'readonly':reads,'evidence':str(output)}


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--root',type=Path,required=True)
    cli.add_argument('--output',type=Path);cli.add_argument('--serve',action='store_true');args=cli.parse_args()
    if args.serve:
        # Solo para revisión manual en navegador. No inicializa cuentas.
        server=create_server(root=args.root,port=0,refresh_interval=60,chat_provider=NoModel())
        print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/#simulacion','root':str(args.root.resolve())}),flush=True)
        try:server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:pass
        finally:server.server_close()
    else:
        if args.output is None:cli.error('--output es obligatorio para el ensayo')
        print(json.dumps(check(args.root,args.output),ensure_ascii=False,indent=2))


if __name__=='__main__':main()

"""Read preserved native files and a frozen reference; no backtest, account or HTTP."""
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
import csv
import gzip
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from trading_ai.execution_comparison import POLICY, compare, mapping_template, normalize_csv
from trading_ai.tv_contracts import checksum

archive=root/'.local/jforex/prueba-historica-01/revision-completa-bfa8d81bdb7f'
native=archive/'native-export'
reference_dir=root/'.local/dukascopy-research/4e59e20a16b74fc7bd16ea7dad80d02d'
price_dir=root/'.local/dukascopy/prices-2d270636ded54ffea90922ef1e75714f'
out=root/'reports/phase6-jforex-native-review-2026-10-23'
assert not out.exists(), 'Do not overwrite delivered evidence'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):return sha256(path.read_bytes()).hexdigest()
def rows(name):
    with (native/name).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def iso(value):return value.isoformat(timespec='milliseconds').replace('+00:00','Z')
def money(value):return Decimal(value.replace('\u2019','').replace('\u00a0',''))

archive_manifest=read(archive/'archive-manifest.json')
for entry in archive_manifest['files']:
    assert digest(archive/entry['file'])==entry['sha256']
meta=read(native/'metadata.json')
assert meta['engine_type']=='TEST' and meta['strategy_revision']=='sma_utc_test_v2_native_calendar'
assert meta['strategy_window_end_observed'] and not meta['has_failure']
assert not (native/'failure.txt').exists()
reference=read(reference_dir/'simulation.json')
refdaily=read(reference_dir/'input-daily.json')
for filename in ('simulation.json','input-manifest.json','input-daily.json'):
    assert (reference_dir/filename).read_bytes()==(root/'reports/phase6-jforex-strategy-2026-10-22/python-reference'/filename).read_bytes()
assert digest(archive/'strategy-reviewed.java')==digest(root/'integrations/jforex/TiresiasSmaUtcTester.java')

prior={}
for path in sorted((root/'reports').rglob('manifest.json')):
    entries=read(path).get('evidence_sha256')
    if not isinstance(entries,dict):continue
    for name,expected in entries.items():
        target=(path.parent/name).resolve()
        assert target.is_relative_to(root) and digest(target)==expected,(path,name)
    prior[path.relative_to(root).as_posix()]={'sha256':digest(path),'files_verified':len(entries)}
previous=read(root/'reports/phase6-jforex-native-calendar-2026-10-23/manifest.json')
for name,expected in previous['unchanged_prior_source_sha256'].items():assert digest(root/name)==expected,name
assert digest(root/'docs/PROJECT_STATUS.md')=='9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb'
for ref in ('HEAD','origin/main'):
    assert subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip()==previous['published_base_commit']

# The native calendar log contains whole hourly interpolation intervals in this
# specific 4-OHLC experiment. Derive eligible hours without using reference dates.
calendar=rows('calendar.csv')
intervals=[]
for row in calendar:
    first=instant(row['first_skipped_tick_at']);last=instant(row['last_skipped_tick_at'])
    start=first.replace(minute=0,second=0,microsecond=0)
    end=last.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    assert first-start==timedelta(seconds=450) and last.replace(microsecond=0).minute==52
    assert int((end-start).total_seconds()/3600)*4==int(row['skipped_ticks'])
    intervals.append((start,end))
assert sum(int(row['skipped_ticks']) for row in calendar)==meta['offline_ticks_skipped']==9880
hourly=rows('hourly.csv')
eligible=[row for row in hourly if not any(first<=instant(row['open_at'])<last for first,last in intervals)]
eligible_opens={row['open_at'] for row in eligible}
excluded=[row for row in hourly if row['open_at'] not in eligible_opens]
assert len(hourly)==8592 and len(eligible)==6122 and len(excluded)==2470
assert all(Decimal(r['bid_volume'])==Decimal(r['ask_volume'])==0 and
           all(len({r[f'{side}_{field}'] for field in ('open','high','low','close')})==1 for side in ('bid','ask')) for r in excluded)
raw=json.loads(gzip.decompress((price_dir/'raw/00.json.gz').read_bytes()),parse_float=Decimal)
start,end=instant('2025-01-01T00:00:00Z'),instant('2025-12-25T00:00:00Z')
expected={datetime.fromtimestamp(r['ts'],UTC):r for r in raw if start<=datetime.fromtimestamp(r['ts'],UTC)<end}
actual={instant(r['open_at']):r for r in eligible}
assert actual.keys()==expected.keys()
field_map={'bid_open':'o','bid_high':'h','bid_low':'l','bid_close':'c','ask_open':'ao','ask_high':'ah','ask_low':'al','ask_close':'ac'}
hourly_differences=[]
for at in sorted(actual):
    for field,key in field_map.items():
        a,b=Decimal(actual[at][field]),Decimal(str(expected[at][key]))
        if a!=b:hourly_differences.append({'open_at':iso(at),'field':field,'native':str(a),'reference':str(b),'native_minus_reference':str(a-b)})
assert len(hourly_differences)==5 and len({r['open_at'] for r in hourly_differences})==3

# Rebuild the full canonical sessions independently from native H1/calendar data.
days=defaultdict(list)
for row in eligible:days[row['open_at'][:10]].append(row)
sessions=[]
for date,bars in sorted(days.items()):
    first=instant(date+'T00:00:00Z');sides={}
    for side in ('bid','ask'):
        sides[side]={'open':bars[0][side+'_open'],'close':bars[-1][side+'_close'],
                     'high':str(max(Decimal(b[side+'_high']) for b in bars)),
                     'low':str(min(Decimal(b[side+'_low']) for b in bars))}
    gaps=[{'from':iso(instant(a['open_at'])+timedelta(hours=1)),'to':iso(instant(b['open_at']))}
          for a,b in zip(bars,bars[1:]) if instant(a['open_at'])+timedelta(hours=1)!=instant(b['open_at'])]
    sessions.append({'date':date,'session_start_at':iso(first),'session_close_at':iso(first+timedelta(days=1)),
        'first_observed_open_at':iso(instant(bars[0]['open_at'])),
        'last_observed_close_at':iso(instant(bars[-1]['open_at'])+timedelta(hours=1)),
        'observed_hours':len(bars),'full_24_hours_observed':len(bars)==24,'internal_gaps':gaps,**sides})
assert checksum(sessions)==reference['sessions_sha256']==checksum(refdaily['sessions'])
daily=rows('daily.csv')
assert len(daily)==len(sessions)==len(reference['observations'])==307
for row,session,observation in zip(daily,sessions,reference['observations'],strict=True):
    assert row['date']==session['date']==observation['date'] and row['boundary_observed']=='true'
    for side in ('bid','ask'):
        for field in ('open','high','low','close'):assert Decimal(row[side+'_'+field])==Decimal(session[side][field])
    for field in ('fast','slow'):
        assert (Decimal(row[field]) if row[field] else None)==(Decimal(observation[field]) if observation[field] is not None else None)
    assert row['signal']==observation['signal']

mapping=mapping_template()
declaration={key:meta[key] for key in ('pair','currency','strategy','fast','slow','start_date','end_date_exclusive')}
declaration.update(producer='JForex TEST, user-supplied HTML and strategy CSV',origin='user_supplied_external',sessions_sha256=checksum(sessions))
policy={**POLICY,'alignment_window_seconds':3600} # One H1 candle for pairing only; time tolerance remains zero.
comparison=compare(reference,normalize_csv((native/'executions.csv').read_bytes(),mapping),policy,declaration)
assert comparison['status']=='differences' and len(comparison['pairs'])==3
assert not any(comparison[key] for key in ('missing','extra','ambiguous','metadata_differences','metadata_unknown','errors'))
for pair in comparison['pairs']:
    assert pair['unknown_fields']==['fee'] and len(pair['differences'])==1
    assert pair['differences'][0]['field']=='executed_at' and pair['differences'][0]['external_minus_python_seconds']==450
executions=rows('executions.csv');orders=rows('orders.csv')
assert sum(Decimal(r['quantity'])*(1 if r['side']=='buy' else -1) for r in executions)==1000
assert [r['state'] for r in orders]==['CLOSED','FILLED']

class Report(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            if self.row is not None:self.row.append(' '.join(' '.join(self.cell).split()))
            self.cell=None
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
parser=Report();parser.feed((archive/'temporary-report.html').read_text(encoding='utf-8-sig'))
two={row[0]:row[1] for row in parser.rows if len(row)==2}
assert not any(len(r)==3 and r[1]=='Exception' for r in parser.rows)
closed=[r for r in parser.rows if len(r)==10 and r[0].startswith('Tiresias_')]
opened=[r for r in parser.rows if len(r)==8 and r[0].startswith('Tiresias_')]
assert len(closed)==len(opened)==1 and two['Account Currency']=='USD'
assert money(two['Initial Equity'])==1000000 and money(two['Final Equity'])==Decimal('999988.68')
cost_after_cutoff=[r for r in parser.rows if len(r)==3 and r[1]=='Overnights' and r[0]>='2025-12-25 00:00:00']
assert len(cost_after_cutoff)==2
summary={
    'native_test_completed_without_strategy_failure':True,'native_strategy_revision':meta['strategy_revision'],
    'initial_equity_usd_reported':str(money(two['Initial Equity'])),
    'final_equity_usd_reported':str(money(two['Final Equity'])),
    'net_change_usd_reported':str(money(two['Final Equity'])-money(two['Initial Equity'])),
    'closed_position_pnl_usd_reported':closed[0][5],'open_position_pnl_usd_reported':opened[0][4],
    'buy_executions':2,'sell_executions':1,'open_quantity_eur_from_fills':'1000',
    'native_processed_ticks':meta['ticks_processed'],'native_offline_ticks_skipped':meta['offline_ticks_skipped'],
    'raw_native_h1':len(hourly),'h1_after_native_calendar':len(eligible),'python_h1':len(expected),
    'h1_missing':0,'h1_extra_after_calendar':0,'h1_ohlc_difference_count':len(hourly_differences),
    'h1_bars_with_price_differences':3,'daily_sessions':307,'daily_ohlc_sma_signal_differences':0,
    'independently_reconstructed_sessions_sha256':checksum(sessions),
    'exact_fill_price_quantity_signal_matches':3,'each_fill_time_native_minus_python_seconds':450,
    'time_tolerance_seconds':0,'alignment_window_seconds':3600,
    'comparison_status':'differences','per_execution_fee_available':False,
    'native_report_commission_usd_reported':two['Commission Fees'],
    'sum_native_order_aggregate_commission_usd_reported':str(sum(Decimal(r['aggregate_commission_usd']) for r in orders)),
    'commission_display_difference_requires_reconciliation':True,
    'native_last_tick_reported':two['Last tick time'],'python_valuation_at':reference['summary']['last_valuation_at'],
    'native_swap_events_after_strategy_cutoff':len(cost_after_cutoff),
    'final_equity_comparable_at_same_cutoff':False,
    'order_amount_column_caveat':'v2 remaining_amount_millions is raw IOrder.getAmount; closed order still reports 0.001, use fill net and native state for open exposure',
    'native_source_bytes_independently_attested_by_platform':False,
    'native_final_report_reconciled':False,'external_equivalence_verified':False,
    'original_files_sha256':{item['file']:item['sha256'] for item in archive_manifest['files']},
}
out.mkdir()
def put(name,raw):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
def save(name,value):put(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
save('native-summary.json',summary)
save('hourly-price-differences.json',hourly_differences)
save('execution-comparison-review.json',{'reference_run':'4e59e20a16b74fc7bd16ea7dad80d02d','reference_sha256':reference['result_sha256'],
    'csv_sha256':digest(native/'executions.csv'),'mapping':mapping,'policy':policy,'declaration':declaration,'comparison':comparison,
    'saved_to_app':False,'accounting_processed':False,'external_equivalence_verified':False,
    'alignment_policy_reason':'One declared H1 candle for unique pairing; all 450-second differences remain visible with zero time tolerance.'})
save('prior-evidence-audit.json',prior)
put('review-source.py',Path(__file__).read_bytes())
put('README.md','''# FASE 6: primer ensayo nativo completo de JForex

El usuario aporta el HTML y los archivos de la revisión v2 del tester. La prueba
completa la ventana prevista sin fallos de estrategia. Se omiten 9.880 ticks de
mercado cerrado y se procesan 24.488. Hay dos compras y una venta de 1.000 EUR,
con una posición final abierta de 1.000 EUR. El HTML informa de 999.988,68 USD
frente a 1.000.000 USD iniciales: pérdida global de 11,32 USD. La posición cerrada
muestra -13,24 USD y la abierta +1,98 USD. Son cifras del informe y su corte final.

El calendario nativo permite seleccionar 6.122 H1 entre las 8.592 exportadas, con
las mismas aperturas horarias que la referencia. Se observan cinco diferencias de
precio en tres velas (archivo separado). No cambian los OHLC diarios: las 307
sesiones reconstruidas independientemente producen exactamente el SHA-256 de la
referencia. Coinciden las SMA y las señales de todas las sesiones.

Las tres ejecuciones coinciden en dirección, cantidad, precio y fecha de señal.
Cada ejecución nativa ocurre 450 segundos después de la apertura asumida por
Python. El contraste conserva esa diferencia con tolerancia temporal cero; una
ventana de una vela H1 se usa únicamente para emparejar candidatos únicos.
Las comisiones por fill siguen desconocidas y no se asignan las agregadas.

La comisión mostrada por el HTML (0,06 USD) y la suma de agregados de órdenes
(0,05 USD) difieren al nivel de presentación disponible. Los swaps ajustan los
precios mostrados de las posiciones; el historial de fills mantiene los precios
originales. Además, el tester llega al 27/12 y registra dos swaps después del corte
de estrategia del 25/12. No se compara su patrimonio final directamente con el
de Python al 25/12 ni se declara contabilidad final reconciliada.

El campo v2 `remaining_amount_millions` reproduce IOrder.getAmount: una orden
CLOSED conserva 0,001. La exposición abierta se verifica mediante saldo de fills
y estado nativo, sin sumar ese campo de órdenes cerradas como posición restante.

Los HTML, mensajes y CSV originales se conservan byte a byte en `.local/`, con
huellas aquí y sin publicar identificadores de cuenta. Este documento registra
una revisión de resultados; no implementa ni valida un importador HTML genérico.
No crea cuentas, operaciones, backtests Python, solicitudes al modelo ni registros
en el comparador de la app. No repite las 35 pruebas de código ya aprobadas: no
cambia el adaptador. Las verificaciones de datos/ejecuciones se ejecutan mediante
el script conservado. Todas las evidencias anteriores, el código de motores y
PROJECT_STATUS permanecen intactos. Sin commit/push ni cierre de FASE 6.

Siguiente paso: conciliar comisiones, swaps y valoración al mismo corte temporal,
y después incorporar esta evidencia nativa al flujo de contraste de la aplicación.
La equivalencia completa de motores o resultados permanece sin verificar.
'''.encode('utf-8'))
manifest={
    'date':'2026-10-23','phase_closed':False,'this_increment_committed':False,'this_increment_pushed':False,
    'published_base_commit':previous['published_base_commit'],
    'native_v2_execution_observed':True,'native_v2_completed':True,'native_confirmed_executions':3,
    'h1_price_differences':5,'daily_sessions_match':307,'fill_time_differences_seconds':[450,450,450],
    'native_final_report_reconciled':False,'external_equivalence_verified':False,
    'own_native_tests_started':0,'own_model_requests':0,'new_python_backtests':0,'tests_rerun':False,
    'previous_jforex_tests_passed':35,'prior_manifest_count':len(prior),
    'unchanged_prior_source_sha256':previous['unchanged_prior_source_sha256'],
    'unchanged_java_sha256':digest(root/'integrations/jforex/TiresiasSmaUtcTester.java'),
    'reference_sha256':reference['result_sha256'],
    'evidence_sha256':{p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file()},
}
save('manifest.json',manifest)
for name,expected_hash in manifest['evidence_sha256'].items():assert digest(out/name)==expected_hash
print(json.dumps({'report':out.relative_to(root).as_posix(),'prior_manifests_verified':len(prior),'evidence_files':len(manifest['evidence_sha256']),
    'net_change_usd':summary['net_change_usd_reported'],'daily_matches':307,'h1_price_differences':5,'fill_matches_with_time_differences':3,
    'manifest_sha256':digest(out/'manifest.json')},ensure_ascii=True))

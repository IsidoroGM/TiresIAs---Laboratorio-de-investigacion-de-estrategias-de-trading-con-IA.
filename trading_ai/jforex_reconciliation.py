"""Review our TEST export and native HTML without executing HTML or trading.

This is a bounded adapter for Tiresias H1/4-OHLC exports, not arbitrary JForex
reports. Reported amounts, reconstructions and missing evidence stay distinct.
"""
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from html.parser import HTMLParser
from itertools import islice
import csv
import io
from pathlib import Path
import re
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from trading_ai.dukascopy_backtest import read_bounded
from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.execution_comparison import POLICY, compare, mapping_template, normalize_csv
from trading_ai.tv_contracts import canonical, checksum, decimal_text, hash_id, number, safe_under, strict_json

PROTOCOL = "tiresias_jforex_reconciliation_v1"
REQUIRED = {"report.html", "metadata.json", "daily.csv", "hourly.csv", "calendar.csv", "events.csv", "executions.csv", "orders.csv"}
OPTIONAL = {"account-snapshots.csv", "order-snapshots.csv"}
MAX_ZIP, MAX_TOTAL = 2*1024*1024, 4*1024*1024


def moment(value):
    from trading_ai.tv_contracts import instant
    return datetime.fromisoformat(instant(value).replace("Z", "+00:00"))


def stamp(value): return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def decimal(value, *, signed=False):
    return number(value, "importe JForex", minimum=Decimal("-1e12") if signed else Decimal(0), maximum=Decimal("1e12"))


def unpack(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_ZIP: raise ValueError("Paquete ZIP de JForex entre 1 byte y 2 MiB requerido.")
    try:
        with ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist(); names=[entry.filename for entry in entries]
            if (len(names)!=len(set(names)) or not REQUIRED <= set(names) <= REQUIRED|OPTIONAL
                    or any(entry.is_dir() or entry.flag_bits & 1 or entry.file_size > 2*1024*1024 for entry in entries)
                    or sum(entry.file_size for entry in entries)>MAX_TOTAL):
                raise ValueError("ZIP incompatible: archivos requeridos en la raíz, sin duplicados, cifrado ni rutas adicionales.")
            return {entry.filename:archive.read(entry) for entry in entries}
    except (BadZipFile, RuntimeError, NotImplementedError, EOFError) as error:
        raise ValueError("ZIP JForex inválido o no admitido.") from error


def table(raw, columns, maximum=20000):
    try:
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),strict=True)
        headers=reader.fieldnames
        if not headers or len(headers)!=len(set(headers)) or not set(columns)<=set(headers): raise ValueError("Cabecera CSV nativa incompatible.")
        values=[]
        for row in reader:
            if len(values)>=maximum or None in row or any(value is None or len(value)>2048 for value in row.values()):
                raise ValueError("CSV nativo excesivo o desalineado.")
            values.append(row)
        return values
    except (csv.Error, UnicodeError) as error: raise ValueError("CSV nativo inválido.") from error


class NativeHTML(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.rows=[]; self.row=None; self.cell=None; self.skipped=0
        try: self.feed(raw.decode("utf-8-sig"))
        except (UnicodeError, RecursionError) as error: raise ValueError("HTML nativo inválido.") from error

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.skipped+=1
        if self.skipped:return
        if tag=="tr":self.row=[]
        if tag in ("td","th"):self.cell=[]

    def handle_data(self, data):
        if self.cell is not None and not self.skipped:self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("script","style"):self.skipped=max(0,self.skipped-1);return
        if self.skipped:return
        if tag in ("td","th") and self.cell is not None:
            value=" ".join(" ".join(self.cell).split())
            if len(value)>4096:raise ValueError("Celda HTML excesiva.")
            if self.row is not None:self.row.append(value)
            self.cell=None
        if tag=="tr" and self.row is not None:
            if len(self.rows)>=5000:raise ValueError("Informe HTML excesivo.")
            self.rows.append(self.row);self.row=None

    def value(self, key):
        values=[row[1] for row in self.rows if len(row)==2 and row[0]==key]
        if len(values)!=1:raise ValueError("Campo HTML ausente o repetido: "+key)
        return values[0]

    def amount(self, key):
        # This supported report profile explicitly uses apostrophe grouping and dot decimals.
        value=self.value(key)
        if not re.fullmatch(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:[\u2019'][0-9]{3})+)(?:\.[0-9]+)?",value):
            raise ValueError("Formato numérico HTML no admitido: "+key)
        return decimal(value.replace("\u2019","").replace("'",""),signed=True)


def native_sessions(files):
    hours=table(files["hourly.csv"],["open_at"]+[side+"_"+field for side in ("bid","ask") for field in ("open","high","low","close")])
    intervals=[]
    for row in table(files["calendar.csv"],["first_skipped_tick_at","last_skipped_tick_at","skipped_ticks"],1000):
        first,last=moment(row["first_skipped_tick_at"]),moment(row["last_skipped_tick_at"])
        start=first.replace(minute=0,second=0,microsecond=0);end=last.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
        if (first-start!=timedelta(seconds=450) or end-last!=timedelta(seconds=450)
                or not row["skipped_ticks"].isdigit() or int(row["skipped_ticks"])!=(end-start).total_seconds()/900
                or first>last or intervals and start<intervals[-1][1]):raise ValueError("Intervalos de calendario incompatibles con H1/4 OHLC.")
        intervals.append((start,end))
    days=defaultdict(list); previous=None; excluded=0
    for row in hours:
        at=moment(row["open_at"])
        if at.minute or at.second or at.microsecond or previous is not None and at<=previous:raise ValueError("H1 repetidas, desordenadas o no horarias.")
        previous=at
        for side in ("bid","ask"):
            prices={key:decimal(row[side+"_"+key]) for key in ("open","high","low","close")}
            if min(prices.values())<=0 or prices["high"]<max(prices.values()) or prices["low"]>min(prices.values()):raise ValueError("OHLC nativo inválido.")
        if any(first<=at<last for first,last in intervals):excluded+=1;continue
        days[at.date().isoformat()].append(row)
    result=[]
    for date,bars in sorted(days.items()):
        start=moment(date+"T00:00:00Z");sides={}
        for side in ("bid","ask"):
            sides[side]={"open":bars[0][side+"_open"],"close":bars[-1][side+"_close"],
                         "high":decimal_text(max(decimal(row[side+"_high"]) for row in bars)),
                         "low":decimal_text(min(decimal(row[side+"_low"]) for row in bars))}
        gaps=[{"from":stamp(moment(a["open_at"])+timedelta(hours=1)),"to":stamp(moment(b["open_at"]))}
              for a,b in zip(bars,bars[1:]) if moment(a["open_at"])+timedelta(hours=1)!=moment(b["open_at"])]
        result.append({"date":date,"session_start_at":stamp(start),"session_close_at":stamp(start+timedelta(days=1)),
            "first_observed_open_at":stamp(moment(bars[0]["open_at"])),"last_observed_close_at":stamp(moment(bars[-1]["open_at"])+timedelta(hours=1)),
            "observed_hours":len(bars),"full_24_hours_observed":len(bars)==24,"internal_gaps":gaps,**sides})
    if not result:raise ValueError("El paquete no contiene sesiones admitidas.")
    return result,{"raw_h1":len(hours),"excluded_h1":excluded,"eligible_h1":len(hours)-excluded}


def reconcile(reference, files, *, html_timezone):
    if html_timezone!="UTC":raise ValueError("Este perfil requiere declarar UTC para las fechas del HTML; se contrastan con los fills ISO.")
    with localcontext(Context(prec=64)):
        return _reconcile(reference,files)


def _reconcile(reference, files):
    meta=strict_json(files["metadata.json"])
    if (not isinstance(meta,dict) or meta.get("protocol") not in ("tiresias_jforex_test_export_v2","tiresias_jforex_test_export_v3")
            or meta.get("engine_type")!="TEST" or meta.get("pair")!="EUR/USD" or meta.get("currency")!="USD"
            or meta.get("strategy")!="sma" or meta.get("declared_feed")!="candles_h1_4ohlc_bid"
            or meta.get("has_failure") is not False or meta.get("strategy_window_end_observed") is not True):
        raise ValueError("Se requiere una exportación TEST H1/4-OHLC BID completada, EUR/USD en USD.")
    html=NativeHTML(files["report.html"])
    if html.value("Account Currency")!="USD":raise ValueError("El HTML no corresponde a una cuenta USD.")
    parameter_keys={"startDate":"start_date","endDateExclusive":"end_date_exclusive","fast":"fast","slow":"slow",
                    "quantityEur":"quantity_eur","expectedCapitalUsd":"expected_initial_capital_usd","declaredFeed":"declared_feed"}
    for name,key in parameter_keys.items():
        if key not in meta:raise ValueError("Parámetro nativo ausente: "+key)
        actual=html.value(name);expected=str(meta[key])
        if name in ("fast","slow","quantityEur","expectedCapitalUsd"):
            if decimal(actual)!=decimal(expected):raise ValueError("HTML y exportación difieren: "+name)
        elif actual!=expected:raise ValueError("HTML y exportación difieren: "+name)
    capital=html.amount("Initial Equity")
    if capital!=decimal(meta["expected_initial_capital_usd"]):raise ValueError("Capital HTML distinto al exigido por la estrategia.")
    cutoff=moment(meta["end_date_exclusive"]+"T00:00:00Z")
    config=reference["configuration"]
    if (any(type(meta[key]) is not int or meta[key]!=config[key] for key in ("fast","slow"))
            or meta['start_date']!=reference['source']['start_date'] or meta['end_date_exclusive']!=reference['source']['end_date_exclusive']
            or capital!=decimal(config['initial_capital']) or decimal(str(meta['quantity_eur']))!=decimal(config['quantity'])):
        raise ValueError("La referencia debe tener el mismo período, SMA, capital y cantidad que JForex.")
    sessions,coverage=native_sessions(files)
    if sessions[0]["date"]<meta["start_date"] or sessions[-1]["date"]>=meta["end_date_exclusive"]:raise ValueError("Sesiones fuera del período declarado.")
    daily=table(files["daily.csv"],["date","fast","slow","signal","boundary_observed"]+[side+"_"+key for side in ("bid","ask") for key in ("open","high","low","close")],1000)
    if len(daily)!=len(sessions):raise ValueError("Sesiones CSV y H1 no corresponden.")
    daily_differences=[];expected_days={r["date"]:r for r in reference["observations"]}
    for row,session in zip(daily,sessions,strict=True):
        if row["date"]!=session["date"] or row["boundary_observed"]!="true":raise ValueError("Sesión nativa no confirmada o desordenada.")
        for side in ("bid","ask"):
            for key in ("open","high","low","close"):
                if decimal(row[side+"_"+key])!=decimal(session[side][key]):raise ValueError("OHLC diario no reproduce sus H1.")
        other=expected_days.get(row["date"])
        if other is None:daily_differences.append({"date":row["date"],"field":"missing_python_session"});continue
        for key in ("fast","slow","signal"):
            actual=row[key] if key=="signal" else decimal(row[key]) if row[key] else None
            expected=other[key] if key=="signal" else decimal(other[key]) if other[key] is not None else None
            if actual!=expected:daily_differences.append({"date":row["date"],"field":key})
    declared={key:meta[key] for key in ("pair","currency","strategy","fast","slow","start_date","end_date_exclusive")}
    declared.update(producer="JForex TEST: HTML y exportaciones aportadas",origin="user_supplied_external",sessions_sha256=checksum(sessions))
    normalized=normalize_csv(files["executions.csv"],mapping_template())
    comparison=compare(reference,normalized,{**POLICY,"alignment_window_seconds":3600},declared)
    if normalized["errors"]:raise ValueError("Ejecuciones nativas inválidas.")
    fills=table(files["executions.csv"],["native_order_id","side","executed_at","quantity","price"],1000)
    orders=table(files["orders.csv"],["native_order_id","label","state","aggregate_commission_usd"],1000)
    order_ids={r["native_order_id"]:r for r in orders}
    if len(order_ids)!=len(orders) or any(not key for key in order_ids):raise ValueError("Identificadores nativos de orden ausentes o repetidos.")
    for fill in fills:
        if fill["native_order_id"] not in order_ids:raise ValueError("Fill sin orden nativa.")
    by_label={r["label"]:[f for f in fills if f["native_order_id"]==r["native_order_id"]] for r in orders}
    if len(by_label)!=len(orders):raise ValueError("Etiquetas nativas repetidas.")
    html_positions=[r for r in html.rows if len(r) in (8,10) and r[0] in by_label]
    if len(html_positions)!=len(orders):raise ValueError("Posiciones HTML y órdenes CSV no corresponden.")
    for row in html_positions:
        entries=[r for r in by_label[row[0]] if r["side"]=="buy"]
        if not entries or row[2]!="BUY":raise ValueError("Este perfil requiere posiciones largas trazables.")
        html_at=datetime.strptime(row[6 if len(row)==8 else 7],"%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        if html_at!=min(moment(r["executed_at"]) for r in entries):raise ValueError("Hora HTML incompatible con los fills; revisa la zona declarada.")
        exits=[r for r in by_label[row[0]] if r['side']=='sell']
        expected_size=sum((decimal(r['quantity']) for r in entries),Decimal(0))
        if len(row)==8:expected_size-=sum((decimal(r['quantity']) for r in exits),Decimal(0))
        if decimal(row[1])*1000000!=expected_size:raise ValueError("Cantidad HTML distinta del historial nativo.")
        if len(row)==10 and (not exits or datetime.strptime(row[8],'%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)!=max(moment(r['executed_at']) for r in exits)):
            raise ValueError("Cierre HTML distinto del historial nativo.")
    def position(at, selected=fills):
        cash=capital;quantity=Decimal(0)
        for row in sorted(selected,key=lambda r:moment(r["executed_at"])):
            if moment(row["executed_at"])>=at:continue
            size=decimal(row["quantity"]);price=decimal(row["price"])
            if row["side"]=="buy":cash-=size*price;quantity+=size
            elif row["side"]=="sell":cash+=size*price;quantity-=size
            else:raise ValueError("Dirección no admitida.")
            if quantity<0:raise ValueError("La exportación incluye posición corta o historia incompleta.")
        return cash,quantity
    cash,quantity=position(cutoff)
    quote=sessions[-1];mark=decimal(quote["bid"]["close"])
    swaps=[];events=[]
    for row in html.rows:
        if len(row)!=3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",row[0]):continue
        at=datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        if row[1]=="Exception":raise ValueError("El informe nativo contiene una excepción.")
        if row[1]=="Overnights":
            match=re.fullmatch(r"Overnight swap \[([+-]?[0-9]+(?:\.[0-9]+)?)\] points applied to position \[([^,]+), EUR/USD, BUY, ([0-9]+(?:\.[0-9]+)?)\]",row[2])
            if not match or match[2] not in by_label:raise ValueError("Evento de swap no admitido o sin orden.")
            _,size=position(at+timedelta(milliseconds=1),by_label[match[2]])
            if size!=decimal(match[3]):raise ValueError("Cantidad del swap distinta de la posición trazada.")
            swaps.append({"at":stamp(at),"points":match[1],"quantity_eur":match[3],
                          "derived_usd":decimal_text(decimal(match[1],signed=True)*Decimal('0.0001')*size),"before_cutoff":at<cutoff})
        if row[1]=="Commission Fees":
            match=re.fullmatch(r"Commission Fees \[([0-9]+(?:\.[0-9]+)?)\]",row[2])
            if not match:raise ValueError("Evento de comisión no admitido.")
            events.append({"at":stamp(at),"reported_usd":match[1],"before_cutoff":at<cutoff})
    swap_before=sum((decimal(r["derived_usd"],signed=True) for r in swaps if r["before_cutoff"]),Decimal(0))
    swap_after=sum((decimal(r["derived_usd"],signed=True) for r in swaps if not r["before_cutoff"]),Decimal(0))
    fee_html=html.amount("Commission Fees")
    fee_orders=sum((decimal(r["aggregate_commission_usd"]) for r in orders),Decimal(0))
    fee_events=sum((decimal(r["reported_usd"]) for r in events),Decimal(0))
    gross=cash+quantity*mark
    issues=["native_cutoff_equity_not_observed", "per_fill_commission_unknown", "reported_amounts_have_limited_precision"]
    if len({fee_html,fee_orders,fee_events})>1:issues.append("commission_totals_differ")
    if any(not r["before_cutoff"] for r in swaps):issues.append("swaps_after_strategy_cutoff")
    if checksum(sessions)!=reference["sessions_sha256"] or daily_differences:issues.append("session_or_signal_differences")
    if comparison["status"]!="matching_fields_unverified_origin":issues.append("execution_differences_or_unknown_fields")
    if any(moment(r["executed_at"])>=cutoff for r in fills):issues.append("fills_after_strategy_cutoff")
    snapshots=[];order_snapshots=[];snapshot_valuations=[];observed=None
    if meta['protocol']=='tiresias_jforex_test_export_v3':
        if not OPTIONAL<=files.keys():raise ValueError("La exportación v3 requiere sus dos archivos de capturas.")
        snapshots=table(files['account-snapshots.csv'],['reason','observed_at','target_cutoff_at','currency','api_equity','api_base_equity','api_balance_eod','api_values_may_lag','quote_at','bid','ask'],10)
        seen=set()
        for row in snapshots:
            if (row['reason'] not in ('strategy_cutoff','tester_stop') or row['reason'] in seen or row['currency']!='USD'
                    or moment(row['target_cutoff_at'])!=cutoff or row['api_values_may_lag']!='true'
                    or moment(row['quote_at'])!=moment(row['observed_at'])):raise ValueError("Captura de cuenta nativa incompatible.")
            seen.add(row['reason'])
            for key in ('api_equity','api_base_equity','api_balance_eod'):decimal(row[key],signed=True)
            if decimal(row['bid'])<=0 or decimal(row['ask'])<decimal(row['bid']):raise ValueError("Cotización de captura incompatible.")
            if row['reason']=='strategy_cutoff':
                if moment(row['observed_at'])<cutoff:raise ValueError("Captura anterior al corte declarado.")
                observed={**row,'api_net_change_usd':decimal_text(decimal(row['api_equity'],signed=True)-capital),
                          'observed_after_target_seconds':(moment(row['observed_at'])-cutoff).total_seconds(),
                          'exact_cutoff_observation':moment(row['observed_at'])==cutoff,'account_values_may_lag':True}
            elif moment(row['observed_at'])!=datetime.strptime(html.value('Last tick time'),'%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC):
                raise ValueError("La captura final y el último tick del HTML no corresponden.")
        if observed is None:raise ValueError("Falta la captura v3 del corte de estrategia.")
        order_snapshots=table(files['order-snapshots.csv'],['reason','observed_at','target_cutoff_at','native_order_id','state','native_amount_millions','open_quantity_eur_from_history','aggregate_commission_usd','adjusted_open_price','native_profit_loss_usd'],2000)
        snapshot_keys=set()
        for row in order_snapshots:
            key=(row['reason'],row['native_order_id'])
            if (key in snapshot_keys or row['native_order_id'] not in order_ids or not any(row['reason']==a['reason'] and row['observed_at']==a['observed_at'] for a in snapshots)
                    or moment(row['target_cutoff_at'])!=cutoff):raise ValueError("Captura de orden sin cuenta/identidad compatible.")
            snapshot_keys.add(key)
            for field in ('native_amount_millions','open_quantity_eur_from_history','aggregate_commission_usd','adjusted_open_price'):decimal(row[field])
            decimal(row['native_profit_loss_usd'],signed=True)
            subset=by_label[order_ids[row['native_order_id']]['label']]
            _,net=position(moment(row['observed_at'])+timedelta(milliseconds=1),subset)
            if net!=decimal(row['open_quantity_eur_from_history']):raise ValueError("Captura de exposición incompatible con sus fills.")
        if any((a['reason'],order['native_order_id']) not in snapshot_keys for a in snapshots for order in orders):raise ValueError("Faltan capturas de órdenes.")
        issues.remove('native_cutoff_equity_not_observed');issues.append('account_api_values_may_lag')
        if not observed['exact_cutoff_observation']:issues.append('native_cutoff_snapshot_after_target')
        for account in snapshots:
            at=moment(account['observed_at']);api_equity=decimal(account['api_equity'],signed=True)
            snapshot_cash,snapshot_quantity=position(at+timedelta(milliseconds=1))
            snapshot_gross=snapshot_cash+snapshot_quantity*decimal(account['bid'])
            snapshot_swaps=sum((decimal(r['derived_usd'],signed=True) for r in swaps if moment(r['at'])<=at),Decimal(0))
            reported_orders=[r for r in order_snapshots if r['reason']==account['reason']]
            snapshot_fee_orders=sum((decimal(r['aggregate_commission_usd']) for r in reported_orders),Decimal(0))
            snapshot_fee_events=sum((decimal(r['reported_usd']) for r in events if moment(r['at'])<=at),Decimal(0))
            snapshot_scenarios=[]
            for source,fee in (('html_events_to_observation',snapshot_fee_events),('order_snapshot_aggregates',snapshot_fee_orders)):
                reconstructed=snapshot_gross+snapshot_swaps-fee
                snapshot_scenarios.append({'commission_source':source,'commission_usd':decimal_text(fee),
                    'reconstructed_equity_usd':decimal_text(reconstructed),'reconstructed_pnl_usd':decimal_text(reconstructed-capital),
                    'api_minus_reconstructed_usd':decimal_text(api_equity-reconstructed),'native_observation':False})
            snapshot_valuations.append({'reason':account['reason'],'observed_at':account['observed_at'],
                'bid':account['bid'],'open_quantity_eur':decimal_text(snapshot_quantity),
                'api_equity_usd':account['api_equity'],'api_net_change_usd':decimal_text(api_equity-capital),
                'gross_equity_from_fills_usd':decimal_text(snapshot_gross),'derived_swaps_to_observation_usd':decimal_text(snapshot_swaps),
                'reported_order_pnl_sum_usd':decimal_text(sum((decimal(r['native_profit_loss_usd'],signed=True) for r in reported_orders),Decimal(0))),
                'diagnostic_scenarios':snapshot_scenarios,'synchronized_equity_verified':False,
                'account_values_may_lag':True,'scenarios_are_not_certified_bounds':True,
                'matches_html_final_equity':api_equity==html.amount('Final Equity') if account['reason']=='tester_stop' else None})
    # Different fee figures are diagnostic scenarios, not a guaranteed interval.
    scenarios=[]
    if not any(moment(r["executed_at"])>=cutoff for r in fills) and not any(not r["before_cutoff"] and decimal(r["reported_usd"]) for r in events):
        for source,fee in (("html_reported",fee_html),("orders_reported",fee_orders)):
            scenarios.append({"commission_source":source,"commission_usd":decimal_text(fee),
                "reconstructed_equity_usd":decimal_text(gross+swap_before-fee),
                "reconstructed_pnl_usd":decimal_text(gross+swap_before-fee-capital),"native_observation":False})
    return {"protocol":PROTOCOL,"status":"partial_reconciliation","native_protocol":meta["protocol"],
        "currency":"USD","html_timezone_declared":"UTC","cutoff":stamp(cutoff),
        "native_report":{"initial_equity_usd":decimal_text(capital),"final_equity_usd":decimal_text(html.amount("Final Equity")),
            "net_change_usd":decimal_text(html.amount("Final Equity")-capital),"last_tick_reported":html.value("Last tick time")},
        "common_cutoff":{"quote_at":quote["last_observed_close_at"],"bid":decimal_text(mark),"open_quantity_eur":decimal_text(quantity),
            "gross_equity_from_fills_usd":decimal_text(gross),"gross_pnl_from_fills_usd":decimal_text(gross-capital),
            "swap_points_to_price_multiplier":"0.0001","derived_swaps_before_cutoff_usd":decimal_text(swap_before),
            "derived_swaps_after_cutoff_usd":decimal_text(swap_after),"native_equity_observed":observed,
            "diagnostic_scenarios":scenarios,"scenarios_are_not_certified_bounds":True,
            "python_equity_usd":reference["summary"]["final_equity"],"python_assumed_commissions_usd":reference["summary"]["assumed_commissions"]},
        "commissions":{"html_reported_usd":decimal_text(fee_html),"orders_reported_sum_usd":decimal_text(fee_orders),
            "events_reported_sum_usd":decimal_text(fee_events),"per_fill_available":False,"allocated_to_fills":False},
        "coverage":{**coverage,"daily_sessions":len(sessions),"sessions_sha256":checksum(sessions),
            "matches_reference_sessions":checksum(sessions)==reference["sessions_sha256"],"daily_signal_differences":daily_differences},
        "comparison":comparison,"swaps":swaps,"commission_events":events,"issues":issues,
        "account_snapshots":snapshots,"order_snapshots":order_snapshots,"snapshot_valuations":snapshot_valuations,
        "native_final_report_reconciled":False,"external_equivalence_verified":False,"external_origin_authenticated":False,
        "accounting_processed":False,"external_orders_sent":False}


class JForexReconciliations:
    def __init__(self, root):
        self.root=Path(root).resolve();self.directory=safe_under(self.root,".local","jforex-reconciliations")

    def prepare(self, *, run, raw, name, html_timezone):
        if not isinstance(name,str) or not 1<=len(name)<=120 or any(c in name for c in '/\\\x00\r\n:'):raise ValueError("Nombre de ZIP simple requerido.")
        reference=DukascopyResearch(self.root).get(run)
        if reference["status"]!="simulated":raise ValueError("Referencia Python calculada requerida.")
        files=unpack(raw);result=reconcile(reference,files,html_timezone=html_timezone)
        return {**result,"reference_run":run,"reference_sha256":reference["result_sha256"],"file_name":name,
            "zip_sha256":sha256(raw).hexdigest(),"original_files_sha256":{key:sha256(value).hexdigest() for key,value in files.items()}},reference

    def preview(self, **values):
        result,_=self.prepare(**values)
        return {"preview":result,"approval_sha256":checksum(result)}

    def save(self, *, approval_sha256, **values):
        result,_=self.prepare(**values);identity=checksum(result)
        if approval_sha256!=identity:raise ValueError("El paquete, referencia o controles cambiaron; revisa otra vista previa.")
        target=safe_under(self.directory,identity)
        if target.exists():self.get(identity);return {"id":identity,"created":False}
        self.directory.mkdir(parents=True,exist_ok=True)
        if len(list(islice(self.directory.iterdir(),101)))>=100:raise ValueError("Límite de cien conciliaciones nativas.")
        temporary=safe_under(self.directory,"preparing-"+uuid4().hex);temporary.mkdir()
        contents={"original.zip":values["raw"],"reconciliation.json":canonical(result)}
        original=safe_under(self.root,".local","dukascopy-research",result["reference_run"])
        for name in ("simulation.json","input-manifest.json","input-daily.json"):contents["reference-"+name]=read_bounded(safe_under(original,name),8*1024*1024)
        contents["summary.json"]=canonical({"id":identity,"status":result["status"],"file_name":result["file_name"],
            "reference_run":result["reference_run"],"cutoff":result["cutoff"],"native_report_pnl_usd":result["native_report"]["net_change_usd"]})
        manifest={"protocol":PROTOCOL,"id":identity,"evidence_sha256":{name:sha256(raw).hexdigest() for name,raw in contents.items()}}
        for name,raw in {**contents,"manifest.json":canonical(manifest)}.items():
            with safe_under(temporary,name).open('xb') as stream:stream.write(raw)
        self._load(temporary,identity)
        try:temporary.rename(target)
        except FileExistsError:self.get(identity);return {"id":identity,"created":False}
        return {"id":identity,"created":True}

    @staticmethod
    def _load(directory, identity):
        manifest=strict_json(read_bounded(safe_under(directory,"manifest.json"),65536))
        names={"original.zip","reconciliation.json","summary.json","reference-simulation.json","reference-input-manifest.json","reference-input-daily.json"}
        if (not isinstance(manifest,dict) or manifest.get("protocol")!=PROTOCOL or manifest.get("id")!=identity
                or not isinstance(manifest.get("evidence_sha256"),dict) or set(manifest["evidence_sha256"])!=names):raise ValueError("Manifiesto de conciliación incompatible.")
        raw={name:read_bounded(safe_under(directory,name),8*1024*1024) for name in names}
        if any(sha256(raw[name]).hexdigest()!=expected for name,expected in manifest["evidence_sha256"].items()):raise ValueError("Original o evidencia de conciliación alterada.")
        result=strict_json(raw["reconciliation.json"]);reference=strict_json(raw["reference-simulation.json"])
        DukascopyResearch.validate_result(reference)
        if checksum(result)!=identity or sha256(raw['original.zip']).hexdigest()!=result['zip_sha256'] or reference['result_sha256']!=result['reference_sha256']:raise ValueError("Identidad de conciliación incompatible.")
        for name,key in (("reference-input-manifest.json","manifest_sha256"),("reference-input-daily.json","daily_file_sha256")):
            if sha256(raw[name]).hexdigest()!=reference['source'][key]:raise ValueError("Copia de precios alterada.")
        return result

    def get(self, identity):return self._load(safe_under(self.directory,hash_id(identity)),identity)

    def overview(self):
        result=[];warnings=[]
        if self.directory.exists():
            entries=list(islice(self.directory.iterdir(),201))
            if len(entries)>200:warnings.append("Catálogo limitado a 200 conciliaciones.")
            for path in sorted(entries[:200]):
                try:
                    hash_id(path.name)
                    raw=read_bounded(safe_under(path,'summary.json'),65536);summary=strict_json(raw)
                    manifest=strict_json(read_bounded(safe_under(path,'manifest.json'),65536))
                    if (not isinstance(summary,dict) or summary.get('id')!=path.name or not isinstance(manifest,dict)
                            or manifest.get('protocol')!=PROTOCOL or manifest.get('id')!=path.name
                            or not isinstance(manifest.get('evidence_sha256'),dict)
                            or manifest['evidence_sha256'].get('summary.json')!=sha256(raw).hexdigest()):raise ValueError("Resumen de conciliación alterado.")
                    result.append({**summary,"inputs_verified_now":False})
                except (OSError,ValueError,KeyError,TypeError) as error:warnings.append(path.name+": "+str(error))
        return {"reconciliations":result,"warnings":warnings,"metadata_only":True}

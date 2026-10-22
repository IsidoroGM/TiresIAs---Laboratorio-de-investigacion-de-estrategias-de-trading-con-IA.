"""Herramientas locales de FASE 6. python -m trading_ai.tradingview --help."""

import argparse
import csv
import json
import os
from pathlib import Path
import sys

from trading_ai.tv_contracts import canonical, checksum, make_contract, strict_json, validate_contract
from trading_ai.tv_io import BundleRepository, import_csv, preview_csv
from trading_ai.tv_reference import compare_observations, read_bars_csv, run_reference
from trading_ai.tv_simulation import SimulationLedger


ROOT = Path(__file__).resolve().parents[1]


def read(path, maximum=4*1024*1024):
    source = Path(path)
    if not source.is_file() or source.stat().st_size > maximum: raise ValueError("Archivo ausente o mayor del límite permitido.")
    with source.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum: raise ValueError("El archivo creció por encima del límite.")
    return raw


def load(path, maximum=65536): return strict_json(read(path, maximum))


def output(path, value):
    # Un resultado previo nunca se reemplaza de forma implícita.
    raw = canonical(value) + b"\n"
    with Path(path).open("xb") as stream: stream.write(raw)
    return {"output": str(Path(path).resolve()), "sha256": checksum(value)}


def parser():
    cli = argparse.ArgumentParser(description="TiresIAs: contratos, inbox y contabilidad exclusivamente virtuales.")
    cli.add_argument("--root", type=Path, default=ROOT, help="Raíz del espacio local; no cambia por abrir un archivo.")
    commands = cli.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new-contract", help="Escribir un contrato nuevo con configuración explícita.")
    new.add_argument("--strategy", choices=("sma", "ema"), required=True)
    for name in ("fast", "slow"): new.add_argument("--" + name, type=int, required=True)
    for name in ("pair", "ticker", "start", "end", "account", "capital", "quantity", "cost-rate", "output"):
        new.add_argument("--" + name, required=True)
    for name in ("prepare", "register", "reference", "preview-csv", "import-csv"):
        child = commands.add_parser(name)
        child.add_argument("--contract", required=True)
        if name == "register": child.add_argument("--risk", help="JSON de límites independientes del modelo.")
        if name == "reference":
            child.add_argument("--bars", required=True); child.add_argument("--output", required=True)
        if name in ("preview-csv", "import-csv"):
            child.add_argument("--csv", required=True); child.add_argument("--mapping", required=True)
            if name == "preview-csv": child.add_argument("--output", required=True)
            else: child.add_argument("--approve-preview", required=True, help="SHA-256 revisado de la vista previa, no del CSV.")
    verify = commands.add_parser("verify"); verify.add_argument("--bundle", required=True)
    commands.add_parser("overview")
    for name in ("account", "process", "mark", "reconcile"):
        child = commands.add_parser(name); child.add_argument("--account", required=True)
        if name == "account": child.add_argument("--as-of")
        if name == "process": child.add_argument("--limit", type=int, default=1000)
        if name == "mark":
            for field in ("price", "at", "mark-id"): child.add_argument("--" + field, required=True)
        if name == "reconcile":
            child.add_argument("--external", required=True); child.add_argument("--tolerance", default="0.01")
    receipt = commands.add_parser("receipt"); receipt.add_argument("--id", required=True)
    receive = commands.add_parser("receive"); receive.add_argument("--file", required=True)
    compare = commands.add_parser("compare-observations")
    for field in ("reference", "observations", "output"): compare.add_argument("--" + field, required=True)
    compare.add_argument("--tolerance", default="0.00000001")
    serve = commands.add_parser("serve", help="Receptor solo 127.0.0.1; token en TIRESIAS_WEBHOOK_TOKEN; no procesa eventos.")
    serve.add_argument("--port", type=int, default=8766)
    return cli


def execute(args):
    ledger, bundles = SimulationLedger(args.root), BundleRepository(args.root)
    command = args.command
    if command == "new-contract":
        values = {key: getattr(args, key) for key in ("strategy", "fast", "slow", "pair", "ticker", "start", "end", "account", "capital", "quantity", "cost_rate")}
        return output(args.output, make_contract(**values))
    if command in ("prepare", "register", "reference", "preview-csv", "import-csv"):
        contract = validate_contract(load(args.contract))
        if command == "prepare": return bundles.create(contract)
        if command == "register": return ledger.register(contract, None if args.risk is None else load(args.risk))
        if command == "reference": return output(args.output, run_reference(contract, read_bars_csv(read(args.bars))))
        raw, mapping = read(args.csv, 2*1024*1024), load(args.mapping)
        if command == "preview-csv":
            preview = preview_csv(raw, mapping, contract)
            return {**output(args.output, {"preview": preview, "approval_sha256": checksum(preview)}),
                    "approval_sha256": checksum(preview), "valid_rows": len(preview["rows"]), "errors": preview["errors"]}
        return import_csv(args.root, ledger, raw, mapping, contract, approved_preview_sha256=args.approve_preview)
    if command == "overview": return {"simulation": ledger.overview(), "tradingview": bundles.overview(), "external_connection": False}
    if command == "verify": return bundles.get(args.bundle)["manifest"]
    if command == "account": return ledger.account(args.account, as_of=args.as_of)
    if command == "process": return ledger.process(args.account, limit=args.limit)
    if command == "mark": return ledger.mark(args.account, price=args.price, at=args.at, mark_id=args.mark_id)
    if command == "reconcile": return ledger.reconcile(args.account, load(args.external), tolerance=args.tolerance)
    if command == "receipt": return ledger.receipt(args.id)
    if command == "receive": return ledger.receive(read(args.file, 65536), transport="file_import", source={"entrypoint": "explicit_cli"})
    if command == "compare-observations":
        return output(args.output, compare_observations(load(args.reference, 16*1024*1024), load(args.observations, 8*1024*1024), tolerance=args.tolerance))
    if command == "serve":
        from trading_ai.tv_receiver import create_receiver
        receiver = create_receiver(ledger, token=os.environ.get("TIRESIAS_WEBHOOK_TOKEN"), port=args.port)
        print(f"Inbox virtual local: http://127.0.0.1:{receiver.server_port}/events; recepción duradera, sin procesamiento contable.", flush=True)
        try: receiver.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt: pass
        finally: receiver.server_close()
        return {"receiver": "closed"}
    raise ValueError("Comando no implementado.")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        value = execute(args)
        print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, OSError, csv.Error) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__": raise SystemExit(main())

"""Fija una propuesta de desarrollo y verifica su integridad antes de evaluarla."""

import argparse
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import os
from pathlib import Path

from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.experiments import (ExperimentPolicy, run_experiment, validate_assessment,
                                    validate_proposal)
from trading_ai.research import ROOT, RunJournal, _engine_hashes


RESEARCH_FILES = ("results.json", "analysis.json", "analysis_origin.json", "events.jsonl")
EXECUTION_POLICY = {"accounts": "independent_per_partition_and_pair",
                    "carry_positions": False, "carry_signals": False,
                    "indicator_warmup": "inside_each_partition"}


def _json(raw: bytes) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Se requiere un objeto JSON.")
    return value


def _policy(values: dict) -> ExperimentPolicy:
    if not isinstance(values, dict) or set(values) != set(ExperimentPolicy.__dataclass_fields__):
        raise ValueError("Controles incompletos o desconocidos.")
    parsed = dict(values)
    for key in ("cost_rate", "initial_capital", "allocation_fraction"):
        value = parsed[key]
        if value is not None:
            if not isinstance(value, str):
                raise ValueError("Los controles decimales deben guardarse como texto.")
            try:
                parsed[key] = Decimal(value)
            except InvalidOperation as error:
                raise ValueError("Control decimal inválido.") from error
    return ExperimentPolicy(**parsed)


def _code_hashes() -> dict:
    result = _engine_hashes()
    for name in ("validation.py", "holdout.py"):
        result[name] = sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
    return result


def _split(directory: Path) -> tuple[dict, str]:
    raw = (directory / "manifest.json").read_bytes()
    plan = _json(raw)
    if (plan["schema_version"] != 1 or plan["protocol"] != "chronological_holdout_v1"
            or plan["stage"] != "prepared_not_evaluated"
            or plan["pairs"] != list(SUPPORTED_PAIRS)
            or plan["execution_policy"] != EXECUTION_POLICY
            or plan["boundary_rules"] != {"development": "date < cutoff", "evaluation": "date >= cutoff"}
            or set(plan["partitions"]) != {"development", "evaluation"}):
        raise ValueError("Protocolo de separación no admitido.")
    cutoff = date.fromisoformat(plan["cutoff"])
    if cutoff.isoformat() != plan["cutoff"]:
        raise ValueError("Fecha de corte no canónica.")
    for name in ("development", "evaluation"):
        block = plan["partitions"][name]
        if block["file"] != name + ".xml":
            raise ValueError("Nombre de partición no permitido.")
        if sha256((directory / block["file"]).read_bytes()).hexdigest() != block["sha256"]:
            raise ValueError(f"Integridad incorrecta de {name}.")
        first, last = date.fromisoformat(block["first_date"]), date.fromisoformat(block["last_date"])
        if (type(block["observations"]) is not int or block["observations"] < 1 or first > last
                or (name == "development" and last >= cutoff)
                or (name == "evaluation" and first < cutoff)):
            raise ValueError("Cobertura incompatible con el corte.")
    development = plan["partitions"]["development"]
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(directory / "development.xml", pair)
        if (len(rates) != development["observations"]
                or str(rates[0][0]) != development["first_date"]
                or str(rates[-1][0]) != development["last_date"]):
            raise ValueError("Desarrollo no coincide con la cobertura registrada.")
    return plan, sha256(raw).hexdigest()


def _research(directory: Path, split_dir: Path, split: dict) -> tuple[dict, dict]:
    raw = {name: (directory / name).read_bytes() for name in RESEARCH_FILES}
    result = _json(raw["results.json"])
    policy = _policy(result["policy"])
    validate_proposal(result["proposal"], policy)
    if result["experiment_id"] != directory.name:
        raise ValueError("La investigación no coincide con su identificador.")
    events = [json.loads(line) for line in raw["events.jsonl"].splitlines()]
    if not events or events[0]["event"] != "run_started" or events[-1]["event"] != "run_completed":
        raise ValueError("La investigación debe haber terminado correctamente.")
    start = events[0]["data"]
    if (start["engine_sha256"] != _engine_hashes() or start["policy"] != policy.parameters()
            or Path(start["data_path"]).resolve() != (split_dir / "development.xml").resolve()):
        raise ValueError("La investigación no corresponde al código, controles o archivo de desarrollo actuales.")
    if result["source"]["sha256"] != split["partitions"]["development"]["sha256"]:
        raise ValueError("La investigación no usa el bloque de desarrollo registrado.")
    recalculated = run_experiment(split_dir / "development.xml", result["proposal"], policy)
    recalculated["experiment_id"] = directory.name
    if recalculated != result:
        raise ValueError("Los resultados de desarrollo no coinciden con el motor.")
    assessment = _json(raw["analysis.json"])
    validate_assessment(assessment, result)
    origin = _json(raw["analysis_origin.json"])
    completion = events[-1]["data"]
    if completion["assessment"] != assessment or completion["analysis_origin"] != origin:
        raise ValueError("El cierre de la investigación no coincide con su análisis.")
    return result, {name: sha256(content).hexdigest() for name, content in raw.items()}


def _write_exclusive(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def freeze_proposal(split_dir: str | Path, research_dir: str | Path,
                    output_dir: str | Path = ROOT / ".local/holdout") -> Path:
    """Registra una propuesta completada sobre desarrollo. Nunca evalúa el reservado.

    Hashes y registro local detectan modificaciones ordinarias; no son una firma
    ni prueban que un usuario nunca haya consultado evaluación fuera de este flujo.
    """
    journal = RunJournal(Path(output_dir))
    split_dir, research_dir = Path(split_dir).resolve(), Path(research_dir).resolve()
    journal.record("freeze_started", split_dir=str(split_dir), research_dir=str(research_dir))
    try:
        split, split_hash = _split(split_dir)
        result, research_hashes = _research(research_dir, split_dir, split)
        frozen = {"schema_version": 1, "stage": "frozen_not_evaluated",
                  "frozen_at": datetime.now(UTC).isoformat(),
                  "split": {"directory": str(split_dir), "manifest_sha256": split_hash},
                  "research": {"directory": str(research_dir), "sha256": research_hashes},
                  "proposal": result["proposal"], "policy": result["policy"],
                  "development_result": result, "code_sha256": _code_hashes(),
                  "execution_policy": EXECUTION_POLICY,
                  "evaluation_state": "No evaluation metrics computed by this workflow; prior exploration exists."}
        # Releer referencias antes de sellar: no aceptar cambios durante la comprobación.
        if _split(split_dir)[1] != split_hash:
            raise ValueError("El manifiesto cambió durante el registro.")
        for name, expected in research_hashes.items():
            if sha256((research_dir / name).read_bytes()).hexdigest() != expected:
                raise ValueError("La investigación cambió durante el registro.")
        raw = (json.dumps(frozen, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
        checksum = sha256(raw).hexdigest()
        _write_exclusive(journal.directory / "frozen.json", raw)
        _write_exclusive(journal.directory / "frozen.sha256", (checksum + "\n").encode("ascii"))
        journal.record("proposal_frozen", frozen_sha256=checksum)
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        journal.record("freeze_failed", error_type=type(error).__name__, message=str(error)[:500])
        raise ValueError(f"No se pudo fijar la propuesta: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_frozen_proposal(directory: str | Path) -> dict:
    """Verifica sello, datos, investigación y código; no calcula evaluación."""
    directory = Path(directory)
    raw = (directory / "frozen.json").read_bytes()
    checksum = sha256(raw).hexdigest()
    if (directory / "frozen.sha256").read_text(encoding="ascii").strip() != checksum:
        raise ValueError("La propuesta fijada ha cambiado: SHA-256 incorrecto.")
    frozen = _json(raw)
    events = [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]
    if (not events or events[-1]["event"] != "proposal_frozen"
            or events[-1]["data"]["frozen_sha256"] != checksum):
        raise ValueError("Falta un registro completo de la propuesta fijada.")
    if (frozen["schema_version"] != 1 or frozen["stage"] != "frozen_not_evaluated"
            or frozen["execution_policy"] != EXECUTION_POLICY or frozen["code_sha256"] != _code_hashes()):
        raise ValueError("El protocolo o el código han cambiado desde el registro.")
    split_dir = Path(frozen["split"]["directory"])
    split, manifest_hash = _split(split_dir)
    if manifest_hash != frozen["split"]["manifest_sha256"]:
        raise ValueError("El manifiesto ha cambiado desde el registro.")
    research_dir = Path(frozen["research"]["directory"])
    for name in RESEARCH_FILES:
        if sha256((research_dir / name).read_bytes()).hexdigest() != frozen["research"]["sha256"][name]:
            raise ValueError("La investigación ha cambiado desde el registro.")
    result, _ = _research(research_dir, split_dir, split)
    if (result != frozen["development_result"] or result["proposal"] != frozen["proposal"]
            or result["policy"] != frozen["policy"]):
        raise ValueError("La propuesta o los controles no coinciden con desarrollo.")
    return frozen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — fijar una propuesta antes de evaluación")
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze", help="Registrar una investigación completada sobre desarrollo")
    freeze.add_argument("--split", type=Path, required=True)
    freeze.add_argument("--research-run", type=Path, required=True)
    freeze.add_argument("--output-dir", type=Path, default=ROOT / ".local/holdout")
    verify = commands.add_parser("verify", help="Verificar el registro sin calcular evaluación")
    verify.add_argument("--frozen-run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze":
            directory = freeze_proposal(args.split, args.research_run, args.output_dir)
            print(f"Propuesta fijada: {directory / 'frozen.json'}")
        else:
            verify_frozen_proposal(args.frozen_run)
            print("Propuesta y referencias verificadas; evaluación no ejecutada.")
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        parser.exit(1, f"Registro detenido: {error}\n")


if __name__ == "__main__":
    main()

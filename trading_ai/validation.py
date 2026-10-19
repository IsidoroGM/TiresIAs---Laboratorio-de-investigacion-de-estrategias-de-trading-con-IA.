"""Prepara una separación cronológica local; no selecciona ni evalúa estrategias."""

import argparse
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET

from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data/raw/ecb-eurofxref-hist-2026-10-18.xml"
NAMESPACE = "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"


def _parse_cutoff(value: str) -> date:
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError
    except ValueError as error:
        raise argparse.ArgumentTypeError("La fecha debe tener formato YYYY-MM-DD.") from error
    return result


def _partition_xml(days: list[ET.Element]) -> bytes:
    root = ET.Element(f"{{{NAMESPACE}}}Envelope")
    container = ET.SubElement(root, f"{{{NAMESPACE}}}Cube")
    for day in days:
        container.append(deepcopy(day))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def prepare_validation_split(source: str | Path, cutoff: date,
                             output_dir: str | Path = ROOT / ".local/validation") -> Path:
    """Desarrollo < cutoff; evaluación >= cutoff. Ambos bloques deben tener datos.

    Valida los cuatro pares antes de escribir. Conserva referencias originales,
    sin recalcular cruces ni rellenar fechas. Una carpeta nueva por preparación
    evita sobrescribir particiones anteriores. El manifiesto no implica que
    estos datos sean inéditos ni que exista aislamiento de permisos de archivos.
    """
    if type(cutoff) is not date:
        raise ValueError("El corte debe ser una fecha sin hora.")
    path = Path(source)
    raw = path.read_bytes()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise ValueError("XML BCE inválido.") from error
    # El lector existente contrasta fechas, duplicados y referencias de cada par.
    rates_by_pair = {pair: load_ecb_rates(path, pair) for pair in SUPPORTED_PAIRS}
    if path.read_bytes() != raw:
        raise ValueError("Los datos cambiaron durante la preparación; separación cancelada.")
    dates = [day for day, _ in rates_by_pair["EUR/USD"]]
    for rates in rates_by_pair.values():
        if [day for day, _ in rates] != dates:
            raise ValueError("Los pares no comparten las mismas fechas.")
    days = sorted(root.findall(f"./{{{NAMESPACE}}}Cube/{{{NAMESPACE}}}Cube"),
                  key=lambda day: day.attrib["time"])
    boundary = cutoff.isoformat()
    partitions = {
        "development": [day for day in days if day.attrib["time"] < boundary],
        "evaluation": [day for day in days if day.attrib["time"] >= boundary],
    }
    if any(not block for block in partitions.values()):
        raise ValueError("El corte debe dejar observaciones en desarrollo y evaluación.")
    manifest = {
        "schema_version": 1,
        "protocol": "chronological_holdout_v1",
        "stage": "prepared_not_evaluated",
        "cutoff": boundary,
        "boundary_rules": {"development": "date < cutoff", "evaluation": "date >= cutoff"},
        "source": {"path": str(path.resolve()), "sha256": sha256(raw).hexdigest(),
                   "observations": len(dates), "first_date": dates[0].isoformat(),
                   "last_date": dates[-1].isoformat()},
        "pairs": list(SUPPORTED_PAIRS),
        "execution_policy": {"accounts": "independent_per_partition_and_pair",
                             "carry_positions": False, "carry_signals": False,
                             "indicator_warmup": "inside_each_partition"},
        "limitations": ["No strategy has been evaluated by this preparation.",
                        "The source history was already explored in previous phases.",
                        "This split does not establish statistical sufficiency or profitability.",
                        "The future workflow must freeze proposals before evaluation.",
                        "Filesystem permissions do not isolate the evaluation file."],
        "partitions": {},
    }
    contents = {}
    for name, block in partitions.items():
        content = _partition_xml(block)
        contents[name] = content
        manifest["partitions"][name] = {
            "file": name + ".xml", "sha256": sha256(content).hexdigest(),
            "observations": len(block), "first_date": block[0].attrib["time"],
            "last_date": block[-1].attrib["time"],
        }
    directory = Path(output_dir) / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    for name, content in contents.items():
        with (directory / (name + ".xml")).open("xb") as stream:
            stream.write(content)
    with (directory / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
    return directory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — separación cronológica (FASE 4)")
    parser.add_argument("--cutoff", type=_parse_cutoff, required=True,
                        help="Primera fecha permitida en evaluación, YYYY-MM-DD; sin ajuste automático")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/validation")
    args = parser.parse_args(argv)
    try:
        directory = prepare_validation_split(args.data, args.cutoff, args.output_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f"No se pudo preparar la separación: {error}\n")
    print(f"Separación preparada: {directory / 'manifest.json'}")
    print("Sin evaluar estrategias ni consultar IA. Fijar la propuesta antes de evaluar el bloque reservado.")


if __name__ == "__main__":
    main()

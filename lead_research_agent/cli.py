"""Local-only CLI with named errors and atomic file replacement."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, research
from .fixtures import generate
from .report import render, json_report

class InputError(ValueError):
    pass

def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise InputError(f"ParseError: {path}: line {error.lineno}: {error.msg}") from None
    except UnicodeError:
        raise InputError(f"ParseError: {path}: line 1: expected UTF-8 text") from None

def load_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use lra fixtures --out <dir> or provide an input directory")
    records = []
    dates = set()
    for path in sorted(directory.iterdir()):
        if path.name in ("expectations.json", "README.md") or not path.is_file():
            continue
        if path.suffix.lower() != ".json":
            raise InputError(f"SchemaError: {path}: line 1: unsupported file format; use JSON")
        data = read_json(path)
        if isinstance(data, dict):
            data = dict(data)
            data.pop("_comment", None)
        if not isinstance(data, dict) or set(data) != {"synthetic", "label", "as_of", "records"}:
            fields = {"synthetic", "label", "as_of", "records"}
            detail = f"missing fields {sorted(fields - data.keys())}; unknown fields {sorted(data.keys() - fields)}" if isinstance(data, dict) else "expected object"
            raise InputError(f"SchemaError: {path}: line 1: {detail}")
        if type(data["synthetic"]) is not bool or not isinstance(data["label"], str) or not data["label"].strip() or not isinstance(data["records"], list):
            raise InputError(f"SchemaError: {path}: line 1: invalid synthetic, label or records field")
        if not isinstance(data["as_of"], str):
            raise InputError(f"SchemaError: {path}: line 1: as_of must be ISO date text")
        if data["synthetic"] and "synthetic" not in data["label"].lower():
            raise InputError(f"SchemaError: {path}: line 1: synthetic label required")
        for record in data["records"]:
            if isinstance(record, dict) and record.get("synthetic") != data["synthetic"]:
                raise InputError(f"SchemaError: {path}: line 1: synthetic field disagrees with envelope")
        try:
            research(data["records"], data["as_of"])
        except SchemaError as error:
            raise InputError(f"SchemaError: {path}: line 1: {error}") from None
        records.extend(data["records"])
        dates.add(data["as_of"])
    if len(dates) > 1:
        raise InputError("SchemaError: as_of: all input files must use the same explicit date")
    # Empty inputs use a documented fixed sentinel, never the machine clock.
    return records, next(iter(dates), "1970-01-01")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute prospect dossiers from local JSON evidence only.")
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("fixtures", help="Generate 200 labelled synthetic prospects", epilog="Example: lra fixtures --out demo")
    p.add_argument("--out", required=True)
    p = subs.add_parser("run", help="Compute and save dossiers", epilog="Example: lra run --input demo")
    p.add_argument("--input", required=True)
    p.add_argument("--state", default=".lra/results.json")
    p = subs.add_parser("report", help="Render saved results with provenance", epilog="Example: lra report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--state", default=".lra/results.json")
    p.add_argument("--out")
    p = subs.add_parser("qualify", help="List prospects satisfying all four evidence rules", epilog="Example: lra qualify --input demo")
    p.add_argument("--input", required=True)
    p = subs.add_parser("dossier", help="Render one prospect and its evidence", epilog="Example: lra dossier --input demo --id p001")
    p.add_argument("--input", required=True)
    p.add_argument("--id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records. Illustrative inputs; no measured savings.")
            return 0
        if args.command == "report":
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingInput: {path}: first run lra run --input <dir>")
            stored = read_json(path)
            if not isinstance(stored, dict) or "dossiers" not in stored or "as_of" not in stored:
                raise InputError(f"SchemaError: {path}: line 1: expected saved dossiers and as_of")
            # Recompute rather than trusting editable cached totals.
            if not isinstance(stored["dossiers"], list) or any(not isinstance(d, dict) for d in stored["dossiers"]):
                raise InputError(f"SchemaError: {path}: line 1: dossiers must be a list of objects")
            records = [{k: v for k, v in d.items() if k not in ("qualified", "reasons")} for d in stored["dossiers"]]
            result = research(records, stored["as_of"])
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
            return 0
        records, as_of = load_input(args.input)
        result = research(records, as_of)
        if args.command == "run":
            atomic_write(args.state, json_report(result))
            print(result["provenance"]["banner"])
            print(f"Computed {result['totals']['records']} dossiers; {result['totals']['qualified']} qualified. Unmeasured savings are not reported.")
        elif args.command == "qualify":
            selected = research([r for r in records if r["id"] in result["qualified_ids"]], as_of)
            print(json_report(selected), end="")
        else:
            selected = [d for d in result["dossiers"] if d["id"] == args.id]
            if not selected:
                raise InputError(f"MissingProspect: id {args.id!r}: use lra qualify --input <dir> to inspect ids")
            subset = research([{k: v for k, v in selected[0].items() if k not in ("qualified", "reasons")}], as_of)
            print(render(subset, "md"), end="")
        return 0
    except (InputError, SchemaError) as error:
        print(str(error) if isinstance(error, InputError) else f"SchemaError: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"FileError: {error.filename or 'output'}: {error.strerror or error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())

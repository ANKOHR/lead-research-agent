import json
import time
import pytest
from lead_research_agent.cli import main
from lead_research_agent.fixtures import generate, fixture_records, AS_OF

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "Data provenance" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    capsys.readouterr()
    assert main(["report", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["records"] == 0

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n invalid', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "ParseError" in err and "bad.json" in err and "line 2" in err

@pytest.mark.parametrize("command", ["fixtures", "run", "report", "qualify", "dossier"])
def test_cli_smoke_all_subcommands(command, capsys):
    with pytest.raises(SystemExit) as e:
        main([command, "--help"])
    assert e.value.code == 0
    assert "Example:" in capsys.readouterr().out

def test_domain_commands(tmp_path, capsys):
    generate(tmp_path)
    assert main(["qualify", "--input", str(tmp_path)]) == 0
    assert len(json.loads(capsys.readouterr().out)["dossiers"]) == 40
    assert main(["dossier", "--input", str(tmp_path), "--id", "p001"]) == 0
    assert "p001" in capsys.readouterr().out

def test_write_failure_no_partial_file(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    assert main(["run", "--input", "demo"]) == 0
    (tmp_path / "blocked").write_text("existing")
    assert main(["report", "--out", "blocked/report.md"]) == 2
    assert "FileError" in capsys.readouterr().err
    assert (tmp_path / "blocked").read_text() == "existing"
    assert not list(tmp_path.glob("tmp*"))

def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err

def test_schema_drift(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{"wrong": 1}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "SchemaError" in capsys.readouterr().err

def test_cli_determinism(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    assert main(["run", "--input", "demo"]) == 0
    first = (tmp_path / ".lra/results.json").read_bytes()
    assert main(["run", "--input", "demo"]) == 0
    assert first == (tmp_path / ".lra/results.json").read_bytes()

def test_hand_written_five_records(tmp_path, capsys):
    records = fixture_records()[:1] + [fixture_records()[i] for i in (40, 80, 120, 160)]
    (tmp_path / "five.json").write_text(json.dumps({"synthetic": True, "label": "Synthetic five cases", "as_of": AS_OF, "records": records}))
    assert main(["qualify", "--input", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["qualified"] == 1


def test_qualify_totals_reconcile(tmp_path, capsys):
    generate(tmp_path)
    assert main(["qualify", "--input", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["totals"]["records"] == len(report["dossiers"]) == 40
    assert report["totals"]["unqualified"] == 0
    assert report["totals"]["stated_budget_pence"] == 400000
    assert report["provenance"]["synthetic_records"] == 40


def test_handwritten_example():
    from pathlib import Path
    from lead_research_agent.cli import load_input
    from lead_research_agent.core import research
    path = Path(__file__).resolve().parents[1] / "examples" / "five"
    records, as_of = load_input(path)
    report = research(records, as_of)
    assert report["qualified_ids"] == ["one"]
    assert report["totals"]["records"] == 5
    assert report["totals"]["stated_budget_pence"] == 40000


def test_cross_file_duplicates(tmp_path, capsys):
    generate(tmp_path)
    (tmp_path / "duplicate.json").write_bytes((tmp_path / "prospects.json").read_bytes())
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "duplicate" in capsys.readouterr().err


def test_cached_totals_not_trusted(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    assert main(["run", "--input", "demo"]) == 0
    path = tmp_path / ".lra/results.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["totals"]["qualified"] = 999
    path.write_text(json.dumps(stored), encoding="utf-8")
    capsys.readouterr()
    assert main(["report", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["qualified"] == 40


def test_atomic_replace_failure_preserves_output(tmp_path, monkeypatch):
    from lead_research_agent.cli import atomic_write
    import os
    path = tmp_path / "report.md"
    path.write_text("original")
    def fail(*args):
        raise OSError("planted replace failure")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        atomic_write(path, "new")
    assert path.read_text() == "original"
    assert list(tmp_path.iterdir()) == [path]

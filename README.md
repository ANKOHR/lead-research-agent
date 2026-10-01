# Lead Research Agent

A CPU-only Python CLI that computes compact prospect dossiers from explicit local evidence. No network access, model calls, discovery, predictions or estimates. Input claims are not independently verified.

## Quickstart

Python 3.10+ and locally installed setuptools are required. Install without contacting a package index:

```powershell
python -m pip install --no-index --no-build-isolation -e .
lra fixtures --out demo
lra run --input demo
lra report --format md
python -m pytest -q
```

The module entry point also works: `python -m lead_research_agent.cli`. Tests require an existing pytest installation. No third-party runtime dependencies.

## Hypothesis and acceptance

Deterministic, tested qualification rules can give Henry a traceable starting point for technical outbound. The synthetic acceptance set has 200 records in five disjoint groups of 40: eligible, missing need, missing contact, absent consent, zero budget. Exactly p001 through p040 qualify. Four groups have a stated budget of 10,000 pence per record: 160 x 10,000 = 1,600,000 pence in total and 40 x 10,000 = 400,000 qualified pence. These are illustrative input amounts, not earned revenue or measured savings.

Acceptance requires exact totals and eligible IDs, zero false positives against planted labels, byte-identical repeated results, and the full demo under five seconds. BUILD-DONE.txt and EVIDENCE.md record local validation. Synthetic accuracy does not establish real-world accuracy or demand.

## Input format

An input directory contains JSON envelopes. README.md and expectations.json are reserved metadata filenames and are not processed. Other formats are rejected with a named schema error; convert CSV/YAML to JSON first. An empty directory is valid and uses the fixed date 1970-01-01. Files are read in filename order; records are sorted by ID. Real trials are not shipped.

```json
{
  "synthetic": false,
  "label": "Henry's manually entered evidence",
  "as_of": "2026-09-30",
  "records": [{
    "id": "lead-1",
    "name": "Name entered by Henry",
    "company": "Company entered by Henry",
    "source": "C:\\evidence\\notes.md",
    "synthetic": false,
    "entered_by": "Henry",
    "observed_on": "2026-09-29",
    "need": "Explicit need entered by Henry",
    "contact": "",
    "consent": false,
    "budget_pence": 0,
    "notes": "Input shape example only, not shipped real data"
  }]
}
```

The example is illustrative, not a measured prospect. Replace every value with your own evidence before a real trial. `examples/five/prospects.json` contains five hand-written, explicitly synthetic cases.

Envelope fields: synthetic boolean, nonblank label, as_of ISO YYYY-MM-DD, records list, optional _comment header. All files must share as_of. Record fields above are required except notes, which defaults to empty text. Unknown fields fail validation. Text is capped at 10,000 characters per field. IDs, names, companies, sources and entered_by must be nonblank. IDs are unique across all files. Real records require entered_by exactly Henry; record synthetic flags must match the envelope. Synthetic labels must contain the word synthetic.

Qualification requires all four supplied facts: nonblank need, syntactically valid contact email, consent true, and positive stated budget. This is rule-based eligibility, not verified contactability or buying intent. Dates must be strict ISO dates; observed_on cannot exceed the explicit as_of. The machine clock is never consulted. budget_pence must be an integer from 0 to 1,000,000,000,000; booleans, floats and negative amounts fail. Unicode and Windows paths are preserved. Control characters other than newline/tab/carriage return, and the prohibited long dash character, are rejected. Invalid input rejects the entire run; no records are silently dropped.

## Commands

All subcommands have `--help` with examples.

| Command | Example | Output |
| --- | --- | --- |
| fixtures | `lra fixtures --out demo` | 200 synthetic records and independent expectations |
| run | `lra run --input demo --state .lra/results.json` | Validates, computes and atomically saves results |
| report | `lra report --format json --out report.json` | Recomputes cached records and renders md or json |
| qualify | `lra qualify --input demo` | Eligible dossiers with totals and provenance for that subset |
| dossier | `lra dossier --input demo --id p001` | One dossier, reasons and evidence provenance |

Run and report use .lra/results.json by default. Saved totals are recomputed from stored records, never trusted as editable ground truth. Store state and output outside the input directory. Reports include every dossier and its source, observation date, need, contact, consent, budget, notes and rejection reasons.

## Architecture

```text
local JSON -> cli.load_input -> core.validate -> core.research
                                                |
                      atomic state <- JSON report
                                                |
                          report.render -> stdout / atomic file
fixtures.generate -> labelled inputs + independent expectations
```

core.py is pure and has no I/O. cli.py owns parsing, errors and local file operations. fixtures.py generates fixed groups without randomness, so no seed is needed. report.py serializes stable JSON and Markdown. Tests exercise real computations and mutated fixture values.

## Honesty boundary and fixture policy

Every report carries aggregate provenance and every dossier identifies synthetic or Henry-entered real data. Synthetic fixtures have synthetic: true in envelopes and records and a SYNTHETIC label. JSON cannot contain header comments, so _comment is the first field as an in-file header; Markdown uses an HTML header comment. Expectations are independent arithmetic and are never used to compute reports.

Unmeasured time and money savings are refused: there are no savings fields or commands. Budgets are supplied integer amounts, never inferred revenue. No confidence score, enrichment, external verification or prediction is performed. Timing evidence measures local execution only. No real trial results are bundled. Output ordering and fixed dates make repeat runs byte-identical.

## Failure modes

- Malformed JSON: ParseError names the file and decoder line; invalid UTF-8 names line 1.
- Missing input/state: MissingInput with a usage hint, exit 2.
- Schema drift/adversarial fields: SchemaError names the file and field/record. Schema locations use line 1 for the whole JSON envelope, not a claimed exact token location. Cross-file conflicts name the conflicting rule.
- Bad output path: FileError, exit 2. Atomic replacement cleans up temporary files and preserves existing output on write failure. Fixture files are atomic individually, not a directory transaction.
- Local files can be edited: the tool cannot attest that a source exists or that a person consented. Review source evidence yourself.

## Two-week improvement hook and verdict

Start a two-week real-use window when Henry first uses his manually entered data. Keep private trial records outside the repo: start/end date, number of actual runs, hand-checked sample size, incorrect dossier count, and the top failure cause. Primary metric: dossier error rate = incorrect dossiers / hand-checked dossiers. An incorrect dossier has any copied fact, eligibility decision or reason inconsistent with the source and documented rules. Review at least one sample from every actual run; a zero-sized sample is unmeasured, never zero error.

If measured error exceeds 10 percent, fix the top cause and retest, or kill with a recorded reason. If it is not used, record that evidence and kill. No savings claim is allowed without a measured baseline and matched timed runs. The present verdict is **pending the two-week evidence window**, not a fabricated commercial outcome. After that window explicitly record one of: expand for daily use or revenue; integrate for heavy sibling overlap; commercialise if a buyer will pay as-is; maintain as portfolio evidence otherwise; kill if unused or unable to meet acceptance. Record dated evidence and reason in VERDICT.md.

On Windows, if pip says Scripts is not on PATH, add its printed directory to PATH, or use the module entry point. For the current PowerShell session:

```powershell
$taskScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
$env:PATH = "$taskScripts;$env:PATH"
```

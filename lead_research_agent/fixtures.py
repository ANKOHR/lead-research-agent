"""Synthetic fixture groups are constructed explicitly, with no random seed needed."""
import json
from pathlib import Path

AS_OF = "2026-09-30"

def fixture_records():
    records = []
    # Five disjoint groups of 40: eligible, absent need, absent contact,
    # absent consent, zero budget. Four positive-budget groups: 160 * 10000.
    for group in range(5):
        for offset in range(40):
            number = group * 40 + offset + 1
            records.append({"id": f"p{number:03}", "name": f"Synthetic Person {number}",
                "company": f"Synthetic Company {number}", "source": f"synthetic://evidence/{number}",
                "synthetic": True, "entered_by": "fixture generator", "observed_on": AS_OF,
                "need": "Explicit request for technical support" if group != 1 else "",
                "contact": f"person{number}@example.invalid" if group != 2 else "",
                "consent": group != 3, "budget_pence": 10000 if group != 4 else 0,
                "notes": "Synthetic illustrative prospect, not a real lead."})
    return records

def expectations():
    # Hand-computed arithmetic, independent of the research engine.
    return {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth",
            "totals": {"records": 200, "qualified": 40, "unqualified": 160,
                       "stated_budget_pence": 1600000, "qualified_stated_budget_pence": 400000},
            "qualified_ids": [f"p{i:03}" for i in range(1, 41)]}

def generate(out):
    from .cli import atomic_write
    directory = Path(out)
    directory.mkdir(parents=True, exist_ok=True)
    # JSON has no comment syntax; the first field acts as an in-file header.
    atomic_write(directory / "prospects.json", json.dumps({"_comment": "SYNTHETIC fixture data", "synthetic": True, "label": "SYNTHETIC fixture data", "as_of": AS_OF, "records": fixture_records()}, ensure_ascii=False, indent=2) + "\n")
    atomic_write(directory / "expectations.json", json.dumps({"_comment": "SYNTHETIC hand-computed ground truth", **expectations()}, indent=2) + "\n")
    atomic_write(directory / "README.md", "<!-- SYNTHETIC fixture set -->\nAll 200 records are synthetic. No real prospects or measured savings.\n")

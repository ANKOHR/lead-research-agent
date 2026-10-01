import json
from lead_research_agent.core import research
from lead_research_agent.fixtures import fixture_records, expectations, AS_OF
from lead_research_agent.report import render

def result():
    return research(fixture_records(), AS_OF)

def test_report_matches_ground_truth_exact():
    report = json.loads(render(result(), "json"))
    assert report["totals"] == expectations()["totals"]

def test_report_zero_false_positives():
    report = json.loads(render(result(), "json"))
    assert set(report["qualified_ids"]) == set(expectations()["qualified_ids"])

def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        assert "Data provenance: 200 synthetic fixture records; 0 real records entered by Henry" in render(result(), fmt)

def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        text = render(result(), fmt)
        assert "Unmeasured" in text
        assert "not a prediction" in text
        assert "Synthetic illustrative prospect" in text

def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(result(), fmt)

def test_determinism_byte_identical():
    for fmt in ("md", "json"):
        assert render(result(), fmt).encode() == render(research(list(reversed(fixture_records())), AS_OF), fmt).encode()

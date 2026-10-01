import pytest
from lead_research_agent.core import research, SchemaError
from lead_research_agent.fixtures import fixture_records, AS_OF, expectations

def test_fixture_ground_truth_matches_hand_computed():
    result = research(fixture_records(), AS_OF)
    assert result["totals"] == expectations()["totals"]
    assert result["qualified_ids"] == expectations()["qualified_ids"]

@pytest.mark.parametrize("field,value", [("budget_pence", -1), ("budget_pence", True), ("budget_pence", 10**13), ("observed_on", "2027-01-01"), ("name", "x"*10001), ("contact", "bad"), ("consent", "yes"), ("synthetic", 1), ("unexpected", 1), ("name", chr(0x2014))])
def test_rejects_adversarial_values(field, value):
    r = fixture_records()[0]
    r[field] = value
    with pytest.raises(SchemaError, match=field):
        research([r], AS_OF)

def test_duplicate_ids():
    r = fixture_records()[0]
    with pytest.raises(SchemaError, match="duplicate"):
        research([r, r], AS_OF)

def test_handles_unicode_and_long_inputs():
    r = fixture_records()[0]
    r["name"] = "王 Élodie"
    r["notes"] = "é"*9900
    r["source"] = r"C:\Users\Henry\evidence.json"
    assert research([r], AS_OF)["dossiers"][0]["notes"] == r["notes"]

def test_corrupted_fixture_changes_computed_result():
    records = fixture_records()
    records[0]["budget_pence"] = 0
    result = research(records, AS_OF)
    assert result["totals"]["qualified"] == 39
    assert result["totals"]["stated_budget_pence"] == 1590000
    assert "p001" not in result["qualified_ids"]

def test_real_provenance():
    r = fixture_records()[0]
    r.update(synthetic=False, entered_by="Henry")
    assert research([r], AS_OF)["provenance"]["real_records_entered_by_Henry"] == 1


@pytest.mark.parametrize("value", ["20260930", "2026-W40-3", None, 123])
def test_strict_as_of(value):
    with pytest.raises(SchemaError, match="as_of"):
        research([], value)


def test_records_type():
    with pytest.raises(SchemaError, match="records"):
        research({}, AS_OF)

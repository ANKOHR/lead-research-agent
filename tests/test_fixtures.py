import json
from lead_research_agent.fixtures import generate

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.iterdir():
        text = path.read_text(encoding="utf-8")
        assert "synthetic" in text.lower()
        if path.suffix == ".json":
            data = json.loads(text)
            assert data["synthetic"] is True
            assert all(r["synthetic"] for r in data.get("records", []))
        else:
            assert text.startswith("<!-- SYNTHETIC")

"""Render computed evidence with provenance on every report."""
import json

def json_report(result):
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

def safe(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\r", " ").replace("\n", " ")

def markdown_report(result):
    lines = ["# Lead Research Agent", "", result["provenance"]["banner"], "", result["honesty"]["qualification"], "", result["honesty"]["savings"], "", f"As of: {result['as_of']}", "", "## Computed totals", ""]
    lines.extend(f"- {key}: {value}" for key, value in result["totals"].items())
    lines += ["", "Budgets are stated input amounts in integer pence, not revenue or savings.", "", "## Compact dossiers", ""]
    for d in result["dossiers"]:
        lines += [f"### {safe(d['id'])}: {safe(d['name'])} at {safe(d['company'])}",
                  f"- Provenance: {'synthetic' if d['synthetic'] else 'real, entered by Henry'}; source: {safe(d['source'])}; observed: {d['observed_on']}",
                  f"- Eligibility: {'qualified' if d['qualified'] else 'unqualified'}; reasons: {', '.join(d['reasons']) or 'all four input rules satisfied'}",
                  f"- Need: {safe(d['need']) or '(not supplied)'}",
                  f"- Contact: {safe(d['contact']) or '(not supplied)'}; consent: {str(d['consent']).lower()}",
                  f"- Stated budget (pence): {d['budget_pence']}", f"- Notes: {safe(d['notes'])}", ""]
    return "\n".join(lines) + "\n"

def render(result, format):
    return json_report(result) if format == "json" else markdown_report(result)

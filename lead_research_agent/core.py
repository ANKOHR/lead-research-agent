"""Pure qualification rules. Scores, savings and predictions are not measured."""
from datetime import date
import re

class SchemaError(ValueError):
    """An explicit input field violates the schema."""

FIELDS = {"id", "name", "company", "source", "synthetic", "entered_by", "observed_on", "need", "contact", "consent", "budget_pence", "notes"}
REQUIRED = FIELDS - {"notes"}
MAX_TEXT = 10000

def validate(records, as_of):
    if not isinstance(records, list):
        raise SchemaError("records: expected list")
    if not isinstance(as_of, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of):
        raise SchemaError("as_of: expected ISO date YYYY-MM-DD")
    try:
        cutoff = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        raise SchemaError("as_of: expected ISO date YYYY-MM-DD") from None
    seen = set()
    result = []
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        if not isinstance(record, dict):
            raise SchemaError(f"{prefix}: expected object")
        missing = REQUIRED - record.keys()
        unknown = record.keys() - FIELDS
        if missing or unknown:
            raise SchemaError(f"{prefix}: missing fields {sorted(missing)}; unknown fields {sorted(unknown)}")
        for field in FIELDS - {"synthetic", "consent", "budget_pence"}:
            value = record.get(field, "")
            if not isinstance(value, str) or len(value) > MAX_TEXT:
                raise SchemaError(f"{prefix}: {field}: expected text up to {MAX_TEXT} characters")
            if chr(0x2014) in value or any(ord(c) < 32 and c not in "\n\t\r" for c in value):
                raise SchemaError(f"{prefix}: {field}: forbidden control character or em dash")
        for field in ("id", "name", "company", "source", "entered_by"):
            if not record[field].strip():
                raise SchemaError(f"{prefix}: {field}: must not be blank")
        if record["id"] in seen:
            raise SchemaError(f"{prefix}: id: duplicate {record['id']!r}")
        seen.add(record["id"])
        for field in ("synthetic", "consent"):
            if type(record[field]) is not bool:
                raise SchemaError(f"{prefix}: {field}: expected boolean")
        if not record["synthetic"] and record["entered_by"] != "Henry":
            raise SchemaError(f"{prefix}: entered_by: real data must be entered by Henry")
        amount = record["budget_pence"]
        if type(amount) is not int or not 0 <= amount <= 10**12:
            raise SchemaError(f"{prefix}: budget_pence: expected integer from 0 to 1000000000000")
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record["observed_on"]):
                raise ValueError
            observed = date.fromisoformat(record["observed_on"])
        except ValueError:
            raise SchemaError(f"{prefix}: observed_on: expected ISO date") from None
        if observed > cutoff:
            raise SchemaError(f"{prefix}: observed_on: future date relative to as_of {as_of}")
        if record["contact"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", record["contact"]):
            raise SchemaError(f"{prefix}: contact: expected email or empty string")
        result.append(dict(record, notes=record.get("notes", "")))
    return sorted(result, key=lambda r: r["id"])

def research(records, as_of):
    dossiers = []
    for record in validate(records, as_of):
        reasons = []
        if not record["need"].strip():
            reasons.append("no explicit need")
        if not record["contact"]:
            reasons.append("no contact supplied")
        if not record["consent"]:
            reasons.append("consent not recorded")
        if record["budget_pence"] == 0:
            reasons.append("no positive stated budget")
        dossiers.append(dict(record, qualified=not reasons, reasons=reasons))
    qualified = [d for d in dossiers if d["qualified"]]
    synthetic = sum(d["synthetic"] for d in dossiers)
    return {
        "schema_version": 1, "as_of": as_of,
        "provenance": {"synthetic_records": synthetic, "real_records_entered_by_Henry": len(dossiers)-synthetic,
                       "banner": f"Data provenance: {synthetic} synthetic fixture records; {len(dossiers)-synthetic} real records entered by Henry. Input claims are not independently verified."},
        "honesty": {"savings": "Unmeasured: time and money saved are not reported without a measured baseline.",
                    "qualification": "Rule-based eligibility from supplied fields, not a prediction of buying intent."},
        "totals": {"records": len(dossiers), "qualified": len(qualified), "unqualified": len(dossiers)-len(qualified),
                   "stated_budget_pence": sum(d["budget_pence"] for d in dossiers),
                   "qualified_stated_budget_pence": sum(d["budget_pence"] for d in qualified)},
        "qualified_ids": [d["id"] for d in qualified], "dossiers": dossiers,
    }

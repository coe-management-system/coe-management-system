import json
import re
from datetime import datetime, timezone
from pathlib import Path

MAPPINGS_DIR = Path(__file__).parent / "mappings"

REQUIRED_FIELDS_BY_TYPE = {
    "student": ["roll_no", "name", "email", "department", "batch", "group"],
    "department": ["code", "name"],
    "attendance": ["roll_no", "date"],
    "training": ["name", "coe_id", "company_id", "technology_id", "start_date", "end_date", "planned_hours"],
    "certification": ["name", "company_id", "validity_period_months", "cost", "issuing_organization"],
    "certification_attempts": ["student_id", "certification_id", "status"],
    "timetable": ["subject_id", "faculty_id", "batch_id", "room_id", "event_date", "start_time", "end_time"],
    "workload": ["faculty", "type", "work_date", "hours"],
    "report": ["title", "status", "report_type"],
    "lab": ["student_id", "lab_id", "system_id", "activity_type"],
    "project": ["title", "status", "project_type"],
}


def load_mapping_rules(import_type: str = "student") -> dict:
    canonical_type = import_type.lower().strip()
    if canonical_type == "students":
        canonical_type = "student"
    mapping_file = MAPPINGS_DIR / f"{canonical_type}.json"
    if not mapping_file.exists():
        mapping_file = MAPPINGS_DIR / "student.json"
    if not mapping_file.exists():
        mapping_file = MAPPINGS_DIR / "students.json"
    with open(mapping_file, "r") as f:
        return json.load(f)


def _normalize_col_name(name: str) -> str:
    return re.sub(r"[_\-\s]+", " ", str(name).strip().lower())


def map_columns(excel_columns: list, import_type: str = "student") -> dict:
    rules = load_mapping_rules(import_type)
    mapping = {}
    used_canonical = set()

    # Pass 1: Exact matches on variants
    for col in excel_columns:
        if col is None:
            continue
        col_clean = _normalize_col_name(col)
        for canonical_field, variants in rules.items():
            if canonical_field in used_canonical:
                continue
            cleaned_variants = [_normalize_col_name(v) for v in variants]
            if col_clean in cleaned_variants:
                mapping[col] = canonical_field
                used_canonical.add(canonical_field)
                break

    # Pass 2: Substring / partial matches for remaining unmapped columns
    for col in excel_columns:
        if col in mapping or col is None:
            continue
        col_clean = _normalize_col_name(col)
        for canonical_field, variants in rules.items():
            if canonical_field in used_canonical:
                continue
            cleaned_variants = [_normalize_col_name(v) for v in variants]
            for v in cleaned_variants:
                if (len(col_clean) >= 3 and col_clean in v) or (len(v) >= 3 and v in col_clean):
                    mapping[col] = canonical_field
                    used_canonical.add(canonical_field)
                    break
            if col in mapping:
                break

    return mapping


def get_required_fields(import_type: str = "student") -> list[str]:
    canonical_type = import_type.lower().strip()
    if canonical_type == "students":
        canonical_type = "student"
    return REQUIRED_FIELDS_BY_TYPE.get(canonical_type, ["name"])


def detect_missing_required_columns(mapped_fields: list[str], import_type: str = "student") -> list[str]:
    required = get_required_fields(import_type)
    mapped_set = set(mapped_fields)
    return [req for req in required if req not in mapped_set]


def generate_default_value(field: str, row_number: int, record: dict, import_type: str = "student") -> str:
    """
    Generates deterministic, valid default values and derived formulas
    for any missing required columns according to system data model conventions.
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    now_time_str = now.strftime("%H:%M:%S")

    if field == "roll_no" or field == "student_id":
        if record.get("admission_id"):
            return str(record["admission_id"]).strip()
        if record.get("registration_no"):
            return str(record["registration_no"]).strip()
        return f"STU{row_number:04d}"

    if field == "name":
        if import_type == "department":
            code = record.get("code", f"DEP{row_number:02d}")
            return f"Department of {code}"
        if import_type == "training":
            return f"Training Program {row_number}"
        if import_type == "certification":
            return f"Certification Track {row_number}"
        return f"Student {row_number}"

    if field == "email":
        roll = record.get("roll_no") or record.get("student_id") or f"student{row_number}"
        clean_roll = re.sub(r"[^a-zA-Z0-9]", "", str(roll)).lower()
        return f"{clean_roll}@institution.edu"

    if field == "department":
        return record.get("branch") or record.get("dept") or "CSE"

    if field == "batch":
        return record.get("year") or record.get("academic_year") or str(now.year)

    if field == "group":
        return record.get("section") or "A"

    if field == "code":
        name = record.get("name", "")
        if name:
            words = name.split()
            code = "".join(w[0] for w in words if w).upper()
            if len(code) >= 2:
                return code[:6]
        return f"DEP{row_number:02d}"

    if field == "status":
        if import_type == "attendance":
            return "Present"
        if import_type == "report":
            return "Submitted"
        return "Active"

    if field == "subject":
        return "CSE101"

    if field in ("date", "work_date", "event_date", "start_date", "due_at", "issue_date"):
        return today_str

    if field in ("end_date", "expiry_date"):
        return f"{now.year + 1}-{now.strftime('%m-%d')}"

    if field in ("start_time", "start"):
        return "09:00:00"

    if field in ("end_time", "end"):
        return "10:00:00"

    if field in ("hours", "planned_hours", "allocated_hours"):
        return "40.0" if import_type == "training" else "1.0"

    if field in ("coe_id", "company_id", "technology_id", "faculty_id", "batch_id", "group_id", "subject_id", "lab_id", "system_id"):
        if field == "system_id":
            return f"SYS-{row_number:02d}"
        return "1"

    if field == "room_id":
        return "101"

    if field == "faculty":
        return f"Faculty Member {row_number}"

    if field in ("type", "activity_type", "project_type", "report_type"):
        if import_type == "workload":
            return "Lecture"
        if import_type == "lab":
            return "Practical"
        if import_type == "project":
            return "Capstone"
        if import_type == "report":
            return "Compliance"
        return "General"

    if field == "validity_period_months":
        return "12"

    if field == "cost":
        return "0.0"

    if field == "issuing_organization":
        return "Institutional Center of Excellence"

    if field == "title":
        return f"{import_type.capitalize()} Item {row_number}"

    if field == "description":
        return f"Auto-configured entry for {import_type} import row {row_number}"

    return ""
"""
Attendance sheet parser — supports BOTH real-world upload shapes.

Format A (wide grid):  one row per student, one column per date
    Serial No. | Roll No. | Admission ID | Student Name | Branch | Section | 01-Aug-2026 | 02-Aug-2026 | ...

Format B (transaction log): one row per attendance event
    Addmission No | Roll No | Subject | Date | Attendance Status

Design rules (from the hardening requirements):
- Format is detected from column headers, never from the filename.
- Each date/status cell is inspected individually (no column-wide dtype
  assumption) and parsed defensively across common formats.
- Unparseable cells are flagged and excluded — never silently coerced to
  today's date or NaT, and never allowed to crash the whole import.
- Marks are normalised case-insensitively (P/p/Present/A/Absent/L/H).
- Duplicate roll/admission ids and duplicate events are reported.
- Out-of-range numeric references (sentinels such as 999999) are flagged,
  never treated as real records.

This module is pure (no DB access) so it can be unit-tested in isolation.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Status canonicalisation
# ---------------------------------------------------------------------------
STATUS_PRESENT = {"p", "present"}
STATUS_ABSENT = {"a", "absent"}
STATUS_LEAVE = {"l", "leave", "od", "on duty", "on-duty", "onduty", "on leave"}
STATUS_HOLIDAY = {
    "h", "holiday", "off", "cancelled", "cancel", "no class",
    "class cancelled", "non-teaching", "non-instructional",
}

UNKNOWN_STATUS_WORDS = {"x", "u", "?", "na", "n/a", "-"}


def _is_blank(value: Any) -> bool:
    """Blank cell check covering None, pandas NaN/NaT and empty strings."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def canonical_status(value: Any) -> tuple[str | None, str]:
    """Map a raw attendance mark to a canonical status.

    Returns (canonical_status, reason). canonical_status is one of
    PRESENT/ABSENT/LEAVE/HOLIDAY, or None when the value cannot be mapped.
    Blank/empty values return (None, "blank").
    """
    if _is_blank(value):
        return None, "blank"
    raw = str(value).strip()
    norm = raw.lower()
    if norm in STATUS_PRESENT:
        return "PRESENT", ""
    if norm in STATUS_ABSENT:
        return "ABSENT", ""
    if norm in STATUS_LEAVE:
        return "LEAVE", ""
    if norm in STATUS_HOLIDAY:
        return "HOLIDAY", ""
    if norm in UNKNOWN_STATUS_WORDS:
        return None, f"unknown mark '{raw}'"
    return None, f"invalid attendance mark '{raw}'"


# ---------------------------------------------------------------------------
# Defensive date parsing (per-cell)
# ---------------------------------------------------------------------------
_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
    "%d-%m-%y", "%d/%m/%y",
    "%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y",
    "%d-%b-%Y", "%d-%b-%y", "%d/%b/%Y", "%d/%b/%y",
    "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d, %Y",
    "%d-%B-%Y", "%d %B, %Y", "%B %d %Y",
)

_DATE_TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
    "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
    "%d-%b-%Y %H:%M", "%d %b %Y %H:%M", "%d %b %Y %I:%M %p",
    "%b %d %Y %I:%M %p", "%m/%d/%Y %I:%M %p",
)

_MONTH_NAMES = set(
    "jan feb mar apr may jun jul aug sep oct nov dec january february march "
    "april may june july august september october november december".split()
)

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_MONTH_NAME_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b", re.IGNORECASE)
_DATE_LIKE_RE = re.compile(
    r"^\s*(\d{1,4})[./-](\d{1,2})[./-](\d{1,4})"
    r"|^\s*\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*"
    r"|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}",
    re.IGNORECASE,
)


def looks_like_date(value: Any) -> bool:
    """Heuristic: does this header/cell look like a date even if it won't parse?"""
    if isinstance(value, (datetime, date)):
        return True
    s = str(value).strip()
    if not s:
        return False
    if _DATE_LIKE_RE.search(s) or _YEAR_RE.search(s) or _MONTH_NAME_RE.search(s):
        return True
    return False


def parse_attendance_date(value: Any, default_year: int | None = None) -> tuple[date | None, str]:
    """Parse a single date value defensively.

    Returns (parsed_date, error_message). A blank cell yields (None, "blank");
    an unparseable value yields (None, "<description>") — the caller must flag
    and exclude, never coerce to today/NaT.
    """
    if _is_blank(value):
        return None, "blank"
    if isinstance(value, datetime):
        return value.date(), ""
    if isinstance(value, date):
        return value, ""

    raw = str(value).strip()
    if not raw:
        return None, "blank"

    cleaned = raw.replace("T", " ").replace(",", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    for fmt in _DATE_TIME_FORMATS + _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date(), ""
        except ValueError:
            continue

    # "MMM DD" / "DD MMM" with no year -> attach the dominant sheet year.
    for fmt in ("%b %d", "%d %b", "%b-%d", "%d-%b"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            if default_year is None:
                default_year = date.today().year
            return parsed.replace(year=default_year), "year-inferred"
        except ValueError:
            continue

    return None, f"unparseable date '{raw}'"


def dominant_year(dates: list[date]) -> int | None:
    """Most common year across a set of parsed dates (for year-less cells)."""
    if not dates:
        return None
    years = [d.year for d in dates]
    return max(set(years), key=years.count)


# ---------------------------------------------------------------------------
# Header classification
# ---------------------------------------------------------------------------
def _norm(name: Any) -> str:
    if name is None:
        return ""
    return re.sub(r"[\s_\-./]+", " ", str(name).strip().lower()).strip()


ROLL_HEADERS = {
    "roll no", "roll", "roll number", "rollnum", "registration no",
    "reg no", "regnum", "enrollment no", "enrolment no", "student id",
    "student no", "std id", "std no", "scholar no", "scholar number",
    "candidate no", "exam roll", "university roll no",
}
ADMISSION_HEADERS = {
    "admission id", "admission no", "admission", "admission number",
    "addmission id", "addmission no", "addmission number",
    "application id", "application no", "enrolment id",
}
NAME_HEADERS = {
    "name", "student name", "student", "full name", "candidate name",
    "candidate", "student's name", "studentname",
}
BRANCH_HEADERS = {
    "branch", "dept", "department", "department name", "branch code",
    "stream", "course", "branch name", "department code", "dept name",
}
SECTION_HEADERS = {
    "section", "group", "class", "section group", "section/group",
    "division", "section name", "group name", "section id",
}
SUBJECT_HEADERS = {
    "subject", "subject code", "subject id", "subject name", "course code",
    "sub code", "subid", "course", "subject_code",
}
STATUS_HEADERS = {
    "attendance status", "status", "attendance", "mark", "marks",
    "p/a", "p/a/l/h", "attendance mark", "attendance marks",
}
RECORD_ID_HEADERS = {
    "record id", "record no", "attendance id", "attendance no",
    "serial no", "sl no", "s no", "slno", "serial number", "trans id",
    "transaction id", "trans no", "transaction no",
}
SERIAL_HEADERS = {"serial no", "sl no", "s no", "slno", "serial number", "s.no", "sl."}
EMAIL_HEADERS = {"email", "email id", "email address", "e mail", "mail", "mail id"}
STATUS_COLUMN_HEADERS = {"status"}  # "status" alone is ambiguous (roster vs attendance)


def classify_header(name: Any) -> str:
    n = _norm(name)
    if not n:
        return "blank"
    if n in STATUS_HEADERS:
        return "status"
    if n in _DATE_HEADERS:
        return "date"
    if n in RECORD_ID_HEADERS:
        return "record_id"
    if n in SERIAL_HEADERS:
        return "serial"
    if n in ADMISSION_HEADERS:
        return "admission"
    if n in ROLL_HEADERS:
        return "roll"
    if n in NAME_HEADERS:
        return "name"
    if n in BRANCH_HEADERS:
        return "branch"
    if n in SECTION_HEADERS:
        return "section"
    if n in SUBJECT_HEADERS:
        return "subject"
    if n in EMAIL_HEADERS:
        return "email"
    if looks_like_date(n):
        return "date"
    return "other"


_DATE_HEADERS = {
    "date", "session date", "attendance date", "class date", "day", "date of class",
}


def classify_headers(headers: list[Any]) -> dict[str, list[Any]]:
    buckets: dict[str, list[Any]] = {
        k: [] for k in ("roll", "admission", "name", "branch", "section",
                        "subject", "date", "status", "record_id", "serial",
                        "email", "other", "blank")
    }
    for h in headers:
        buckets[classify_header(h)].append(h)
    return buckets


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------
def detect_attendance_format(headers: list[Any]) -> dict:
    """Decide which shape the sheet is, from headers alone.

    Returns {"format": "wide"|"transaction"|None,
             "detected_type": "attendance"|"roster"|"unknown",
             "reason": <human readable>}.
    """
    buckets = classify_headers(headers)
    has_roll = bool(buckets["roll"])
    has_admission = bool(buckets["admission"])
    has_name = bool(buckets["name"])
    has_date = bool(buckets["date"])
    has_status = bool(buckets["status"])
    has_subject = bool(buckets["subject"])
    has_email = bool(buckets["email"])

    # A roster has email + Active/Inactive status, but no attendance date/status.
    if has_email and has_status and not has_date:
        return {
            "format": None,
            "detected_type": "roster",
            "reason": "This looks like a student roster (Email + Status columns), "
                      "not an attendance sheet. Expected date and attendance-mark "
                      "columns but found none.",
        }

    if has_status and has_date:
        return {
            "format": "transaction",
            "detected_type": "attendance",
            "reason": "transaction log (Date + Attendance Status columns)",
        }

    if has_date and (has_roll or has_admission):
        if has_roll and has_admission:
            return {
                "format": "wide",
                "detected_type": "attendance",
                "reason": "wide grid (Roll No. + Admission ID + per-date columns)",
            }
        return {
            "format": "wide",
            "detected_type": "attendance",
            "reason": "wide grid (per-date columns)",
        }

    if has_subject and has_roll and has_date:
        return {
            "format": "transaction",
            "detected_type": "attendance",
            "reason": "transaction log (Roll No + Subject + Date)",
        }

    if not has_date and not has_status and not has_roll and not has_admission:
        return {
            "format": None,
            "detected_type": "unknown",
            "reason": "No date, roll-number, admission-id or status columns found. "
                      "Expected an attendance sheet (per-date columns, or "
                      "Date + Attendance Status).",
        }

    return {
        "format": None,
        "detected_type": "unknown",
        "reason": "Could not recognise an attendance layout from the column "
                  "headers. Missing either per-date columns (wide grid) or a "
                  "Date + Attendance Status pair (transaction log).",
    }


# ---------------------------------------------------------------------------
# Filename hint (fallback only — never the primary source of truth)
# ---------------------------------------------------------------------------
_SUBJECT_IN_FILENAME_RE = re.compile(
    r"(?:^|[_\- ])([A-Za-z]{1,4}\d{2,4})(?=_|\-|\.|$)"
)
_BRANCH_IN_FILENAME_RE = re.compile(
    r"(?:^|[_\- ])([A-Za-z]{2,4})(?=_[_\- ]?[a-zA-Z]?\d|_?g\d|\.|$)",
    re.IGNORECASE,
)


def infer_subject_from_filename(filename: str | None) -> tuple[str | None, str | None]:
    """Best-effort subject-code / branch hint from the filename.

    Returns (subject_code_or_None, branch_or_None). Used only when the sheet
    itself does not identify the subject.
    """
    if not filename:
        return None, None
    base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    m = _SUBJECT_IN_FILENAME_RE.search(base)
    subject = m.group(1).upper() if m else None
    branch = None
    bm = _BRANCH_IN_FILENAME_RE.search(base)
    if bm:
        candidate = bm.group(1).upper()
        if candidate in {"CSE", "ECE", "EEE", "IT", "CSDS", "ME", "CE", "AI", "AIDS", "CIVIL", "MECH"}:
            branch = candidate
    return subject, branch


# ---------------------------------------------------------------------------
# Sentinel / out-of-range reference detection
# ---------------------------------------------------------------------------
def is_sentinel_reference(value: Any, threshold: int) -> bool:
    """True for clearly out-of-range numeric references (e.g. 999999)."""
    if value is None:
        return False
    s = str(value).strip()
    if not s.isdigit():
        return False
    try:
        num = int(s)
    except ValueError:
        return False
    if num >= threshold:
        return True
    # All-9 style codes (9999, 999999) below threshold are still suspicious.
    if re.fullmatch(r"9{4,}", s):
        return True
    return False


# ---------------------------------------------------------------------------
# Sheet parsing
# ---------------------------------------------------------------------------
def parse_attendance_sheet(
    df: Any,
    filename: str | None = None,
    subject_hint: str | None = None,
    sentinel_roll_threshold: int = 100000,
    sentinel_subject_threshold: int = 9000,
) -> dict:
    """Parse an attendance DataFrame (type-preserving) into validated events.

    Returns a dict with keys: format, detected_type, reason, headers,
    column_map, subject, subject_source, events, issues, duplicates, summary.
    """
    headers = list(df.columns)
    detection = detect_attendance_format(headers)
    buckets = classify_headers(headers)

    issues: list[dict] = []
    sheet_format = detection["format"]

    if sheet_format is None:
        return {
            "format": None,
            "detected_type": detection["detected_type"],
            "reason": detection["reason"],
            "headers": headers,
            "column_map": {},
            "subject": None,
            "subject_source": None,
            "events": [],
            "issues": [],
            "duplicates": [],
            "summary": {"total_rows": len(df), "events": 0, "flagged_rows": 0},
        }

    # --- column indexes ------------------------------------------------------
    def first_of(bucket: str) -> Any | None:
        if buckets.get(bucket):
            return buckets[bucket][0]
        return None

    roll_col = first_of("roll")
    admission_col = first_of("admission")
    name_col = first_of("name")
    branch_col = first_of("branch")
    section_col = first_of("section")
    subject_col = first_of("subject")
    record_id_col = first_of("record_id")
    status_col = first_of("status")
    date_cols = [h for h in buckets["date"]]
    serial_col = first_of("serial")

    # --- subject resolution (sheet-level) -------------------------------------
    subject = None
    subject_source = None
    if subject_hint:
        subject = str(subject_hint).strip().upper()
        subject_source = "explicit"
    elif subject_col is not None:
        for idx, row in df.iterrows():
            val = row[subject_col]
            if val is not None and str(val).strip():
                subject = str(val).strip().upper()
                subject_source = "column"
                break
    if subject is None:
        subject, _branch_hint = infer_subject_from_filename(filename)
        subject_source = "filename" if subject else None

    # --- wide grid -------------------------------------------------------------
    events: list[dict] = []
    row_issue_count: dict[int, int] = {}

    def _cell_text(row, col) -> str:
        if col is None:
            return ""
        v = row[col]
        return "" if _is_blank(v) else str(v).strip()

    if sheet_format == "wide":
        parsed_dates: list[date] = []
        date_col_pairs: list[tuple[Any, date]] = []
        bad_date_cols: list[tuple[Any, str]] = []

        for h in date_cols:
            d, err = parse_attendance_date(h)
            if d is not None:
                date_col_pairs.append((h, d))
                parsed_dates.append(d)
            elif looks_like_date(h):
                bad_date_cols.append((h, err))

        if not date_col_pairs:
            issues.append({
                "row": 0, "column": None, "type": "no_date_columns",
                "message": "No valid date columns found in the wide-grid sheet",
            })

        fallback_year = dominant_year(parsed_dates) or date.today().year

        seen_rolls: dict[str, list[int]] = {}
        seen_admissions: dict[str, list[int]] = {}

        for idx, row in df.iterrows():
            row_number = idx + 2
            roll = _cell_text(row, roll_col)
            admission = _cell_text(row, admission_col)
            name = _cell_text(row, name_col)

            if not roll and not admission:
                issues.append({
                    "row": row_number, "column": roll_col, "type": "no_student_reference",
                    "message": "Row has neither Roll No. nor Admission ID",
                })
                row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
                continue

            ref = roll or admission
            sentinel = (
                is_sentinel_reference(ref, sentinel_roll_threshold)
            )
            duplicate_ref = False
            if roll:
                seen_rolls.setdefault(roll, []).append(row_number)
                duplicate_ref = len(seen_rolls[roll]) > 1
            if admission and admission != roll:
                seen_admissions.setdefault(admission, []).append(row_number)
                duplicate_ref = duplicate_ref or len(seen_admissions[admission]) > 1

            if sentinel:
                issues.append({
                    "row": row_number, "column": roll_col or admission_col,
                    "type": "sentinel_student",
                    "message": f"Student reference '{ref}' is out of the normal range "
                               f"(>= {sentinel_roll_threshold}) — flagged for review",
                })
            if duplicate_ref:
                issues.append({
                    "row": row_number, "column": roll_col or admission_col,
                    "type": "duplicate_student_in_sheet",
                    "message": f"Student '{ref}' appears more than once in this sheet",
                })

            if name and not name_col:
                pass
            branch = _cell_text(row, branch_col)
            section = _cell_text(row, section_col)

            for h, d in date_col_pairs:
                cell = row[h]
                status, reason = canonical_status(cell)
                event = {
                    "row": row_number,
                    "roll_no": roll,
                    "admission_id": admission,
                    "student_name": name,
                    "branch": branch,
                    "section": section,
                    "subject": subject,
                    "date": d.isoformat(),
                    "status": status,
                    "raw_status": "" if _is_blank(cell) else str(cell).strip(),
                    "external_id": _cell_text(row, record_id_col) or None,
                    "sentinel": sentinel,
                    "duplicate_in_sheet": duplicate_ref,
                    "issues": [],
                }
                if status is None:
                    if reason == "blank":
                        # Not-marked -> exclude from denominator, not absent.
                        event["issues"].append({
                            "type": "not_marked",
                            "message": f"Blank attendance mark on {d.isoformat()} "
                                       "(excluded from classes held)",
                        })
                        issues.append({
                            "row": row_number, "column": h, "type": "not_marked",
                            "message": f"Blank mark on {d.isoformat()} for '{ref}'",
                        })
                    else:
                        event["issues"].append({
                            "type": "invalid_mark",
                            "message": f"Invalid mark '{event['raw_status']}' on "
                                       f"{d.isoformat()} ({reason})",
                        })
                        issues.append({
                            "row": row_number, "column": h, "type": "invalid_mark",
                            "message": f"Row {row_number} {d.isoformat()}: {reason}",
                        })
                    row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
                    events.append(event)  # kept for the audit trail, excluded at commit
                    continue
                events.append(event)

            if subject is None:
                issues.append({
                    "row": row_number, "column": subject_col,
                    "type": "subject_required",
                    "message": "No subject could be determined for this wide-grid sheet; "
                               "add a Subject column, name the file with a subject code, "
                               "or pass a subject explicitly",
                })

        for h, err in bad_date_cols:
            issues.append({
                "row": 0, "column": h, "type": "malformed_date_header",
                "message": f"Date header '{h}' could not be parsed ({err}) — column skipped",
            })

        dup_groups = []
        for ref, rows in {**seen_rolls, **seen_admissions}.items():
            if len(rows) > 1:
                dup_groups.append({"key": ref, "rows": rows, "reason": "duplicate student reference"})

        return _build_result(sheet_format, detection, headers, subject, subject_source,
                             events, issues, dup_groups, len(df), date_col_pairs, bad_date_cols)

    # --- transaction log --------------------------------------------------------
    if roll_col is None and record_id_col is None and admission_col is None:
        issues.append({
            "row": 0, "column": None, "type": "no_student_reference_column",
            "message": "Transaction log is missing a Roll No./Admission ID column",
        })

    seen_events: dict[tuple, list[int]] = {}
    seen_ext_ids: dict[str, list[int]] = {}
    parsed_dates_tx: list[date] = []

    # Pre-scan for year inference from the date column.
    if date_cols:
        for idx, row in df.iterrows():
            d, _err = parse_attendance_date(row[date_cols[0]])
            if d is not None:
                parsed_dates_tx.append(d)
    fallback_year = dominant_year(parsed_dates_tx) or date.today().year

    for idx, row in df.iterrows():
        row_number = idx + 2
        roll = _cell_text(row, roll_col)
        admission = _cell_text(row, admission_col)
        ref = roll or admission
        ext_id = _cell_text(row, record_id_col) or None
        raw_date = row[date_cols[0]] if date_cols else None
        d, date_err = parse_attendance_date(raw_date, fallback_year)
        raw_status_val = row[status_col] if status_col else None
        status, status_reason = canonical_status(raw_status_val)
        subj = _cell_text(row, subject_col).upper() if subject_col else subject

        row_issues: list[dict] = []

        if not ref:
            issues.append({
                "row": row_number, "column": roll_col or record_id_col,
                "type": "no_student_reference",
                "message": "Row has no Roll No./Admission ID",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            continue

        sentinel = is_sentinel_reference(ref, sentinel_roll_threshold) if ref else False
        if sentinel:
            issues.append({
                "row": row_number, "column": roll_col or admission_col,
                "type": "sentinel_student",
                "message": f"Student reference '{ref}' is out of the normal range "
                           f"(>= {sentinel_roll_threshold}) — flagged for review",
            })

        if d is None:
            issues.append({
                "row": row_number, "column": date_cols[0] if date_cols else None,
                "type": "bad_date",
                "message": f"Row {row_number}: {date_err} — row excluded from calculations",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            events.append({
                "row": row_number,
                "roll_no": roll,
                "admission_id": admission,
                "student_name": _cell_text(row, name_col),
                "subject": subj,
                "date": None,
                "status": None,
                "raw_status": "" if _is_blank(raw_status_val) else str(raw_status_val).strip(),
                "external_id": ext_id,
                "sentinel": sentinel,
                "duplicate_in_sheet": False,
                "issues": [{"type": "bad_date", "message": date_err}],
            })
            continue

        if not subj:
            issues.append({
                "row": row_number, "column": subject_col,
                "type": "subject_required",
                "message": f"Row {row_number} has no subject code",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            continue

        if is_sentinel_reference(subj, sentinel_subject_threshold):
            issues.append({
                "row": row_number, "column": subject_col,
                "type": "sentinel_subject",
                "message": f"Subject '{subj}' is out of the normal range "
                           f"(>= {sentinel_subject_threshold}) — flagged for review",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            continue

        if status is None and status_reason != "blank":
            issues.append({
                "row": row_number, "column": status_col,
                "type": "invalid_mark",
                "message": f"Row {row_number}: {status_reason}",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            continue
        if status is None:  # blank status
            issues.append({
                "row": row_number, "column": status_col,
                "type": "not_marked",
                "message": f"Row {row_number}: blank attendance status — excluded",
            })
            row_issue_count[row_number] = row_issue_count.get(row_number, 0) + 1
            continue

        if ext_id:
            seen_ext_ids.setdefault(ext_id, []).append(row_number)
            if len(seen_ext_ids[ext_id]) > 1:
                issues.append({
                    "row": row_number, "column": record_id_col,
                    "type": "duplicate_record_id",
                    "message": f"Record id '{ext_id}' appears more than once in this sheet",
                })

        event = {
            "row": row_number,
            "roll_no": roll,
            "admission_id": admission,
            "student_name": _cell_text(row, name_col),
            "branch": _cell_text(row, branch_col),
            "section": _cell_text(row, section_col),
            "subject": subj,
            "date": d.isoformat(),
            "status": status,
            "raw_status": "" if _is_blank(raw_status_val) else str(raw_status_val).strip(),
            "external_id": ext_id,
            "sentinel": sentinel,
            "duplicate_in_sheet": False,
            "issues": [],
        }
        dup_key = (roll or admission, subj, d.isoformat())
        seen_events.setdefault(dup_key, []).append(row_number)
        if len(seen_events[dup_key]) > 1:
            issues.append({
                "row": row_number, "column": None,
                "type": "duplicate_event",
                "message": f"Duplicate event for ({ref}, {subj}, {d.isoformat()})",
            })
        events.append(event)

    dup_groups = [
        {"key": ref, "rows": rows, "reason": "duplicate event in sheet"}
        for ref, rows in seen_events.items() if len(rows) > 1
    ]
    for ext_id, rows in seen_ext_ids.items():
        if len(rows) > 1:
            dup_groups.append({"key": f"record_id:{ext_id}", "rows": rows, "reason": "duplicate record id"})

    return _build_result(sheet_format, detection, headers, subject, subject_source,
                         events, issues, dup_groups, len(df), [], [])


def _build_result(
    sheet_format: str,
    detection: dict,
    headers: list[Any],
    subject: str | None,
    subject_source: str | None,
    events: list[dict],
    issues: list[dict],
    dup_groups: list[dict],
    total_rows: int,
    date_col_pairs: list[tuple[Any, date]],
    bad_date_cols: list[tuple[Any, str]],
) -> dict:
    invalid_mark_cells = [i for i in issues if i["type"] in ("invalid_mark", "not_marked")]
    flagged_rows = len({i["row"] for i in issues if i["row"]})
    return {
        "format": sheet_format,
        "detected_type": detection["detected_type"],
        "reason": detection["reason"],
        "headers": headers,
        "column_map": {},
        "subject": subject,
        "subject_source": subject_source,
        "date_columns": [h for h, _ in date_col_pairs],
        "bad_date_columns": bad_date_cols,
        "events": events,
        "issues": issues,
        "duplicates": dup_groups,
        "summary": {
            "total_rows": total_rows,
            "events": len(events),
            "valid_events": sum(1 for e in events if not e["issues"] and e["status"]),
            "flagged_rows": flagged_rows,
            "flagged_cells": len(invalid_mark_cells),
            "duplicate_groups": len(dup_groups),
        },
    }

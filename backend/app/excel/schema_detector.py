"""
Schema/dataset-type detection (M2-03).
Given the raw Excel column headers, guesses which import_type the file
represents (student vs department) by scoring header overlap against each
known entity's expected field set. This assists the caller but does not
silently override an explicitly supplied import_type.
"""

STUDENT_SIGNATURE_COLUMNS = {
    "roll_no", "roll no", "roll number", "reg_no", "registration no",
    "student id", "admission id", "name", "student name", "email",
    "department", "batch", "group", "section",
}

DEPARTMENT_SIGNATURE_COLUMNS = {
    "code", "dept code", "department code", "name", "department name",
}


def detect_import_type(excel_columns: list[str]) -> dict:
    """
    Returns a dict with detected_type (str or None), confidence (float 0-1),
    and scores (dict of type -> raw overlap score) so the caller can decide
    whether to trust the guess or require explicit confirmation.
    """
    normalized = {c.strip().lower() for c in excel_columns}

    student_overlap = len(normalized & STUDENT_SIGNATURE_COLUMNS)
    department_overlap = len(normalized & DEPARTMENT_SIGNATURE_COLUMNS)

    scores = {
        "student": student_overlap,
        "department": department_overlap,
    }

    total = student_overlap + department_overlap
    if total == 0:
        return {"detected_type": None, "confidence": 0.0, "scores": scores}

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return {"detected_type": None, "confidence": 0.0, "scores": scores}

    confidence = round(best_score / total, 4) if total > 0 else 0.0

    if scores["student"] == scores["department"]:
        return {"detected_type": None, "confidence": 0.5, "scores": scores}

    return {"detected_type": best_type, "confidence": confidence, "scores": scores}

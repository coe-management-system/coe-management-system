"""
Enhanced schema/dataset-type detection (M2-03).
Given the raw Excel column headers, sheet names, and/or filename,
determines which import_type the file represents.
"""
from pathlib import Path
import json
import re

MAPPINGS_DIR = Path(__file__).parent / "mappings"


def _load_all_signatures() -> dict[str, set[str]]:
    signatures = {}
    for mapping_file in MAPPINGS_DIR.glob("*.json"):
        import_type = mapping_file.stem
        if import_type == "students":
            import_type = "student"
        try:
            with open(mapping_file, "r") as f:
                rules = json.load(f)
                sig = set()
                for canonical, variants in rules.items():
                    sig.add(canonical.lower().strip())
                    for v in variants:
                        sig.add(v.lower().strip())
                signatures[import_type] = sig
        except Exception:
            pass
    return signatures


TYPE_SIGNATURES = _load_all_signatures()

# Add fallback keywords for type detection
KEYWORD_HINTS = {
    "student": ["student", "roll", "admission", "registration", "branch", "batch", "roster", "pupil"],
    "department": ["department", "dept", "academic_master"],
    "attendance": ["attendance", "present", "absent", "session_date", "roll no", "date", "mark", "p/a", "serial no"],
    "training": ["training", "program", "coe", "planned_hours"],
    "certification": ["certification", "certificate", "attempt", "validity"],
    "certification_attempts": ["certification_attempt", "certification attempt", "cert attempt", "attempt", "result", "score", "passed", "failed"],
    "timetable": ["timetable", "schedule", "room", "slot", "conflicts"],
    "workload": ["workload", "allocation", "teaching_hours"],
    "report": ["report", "compliance", "assignment", "submission"],
    "lab": ["lab", "laboratory", "login_at", "logout_at", "system_id"],
    "project": ["project", "resume", "mentor", "capstone"],
}


def _clean_str(s: str) -> str:
    return re.sub(r"[_\-\s]+", " ", str(s).strip().lower())


def detect_import_type(
    excel_columns: list[str],
    filename: str | None = None,
    sheet_name: str | None = None,
) -> dict:
    """
    Returns a dict with detected_type (str or None), confidence (float 0-1),
    and scores (dict of type -> score).
    """
    if not excel_columns:
        return {"detected_type": None, "confidence": 0.0, "scores": {}}

    normalized_cols = {_clean_str(c) for c in excel_columns if c is not None and str(c).strip()}
    
    # Base signature matching
    scores = {}
    all_types = [
        "student", "department", "attendance", "training",
        "certification", "certification_attempts", "timetable", "workload", "report",
        "lab", "project",
    ]

    for t in all_types:
        sig = TYPE_SIGNATURES.get(t, set())
        cleaned_sig = {_clean_str(s) for s in sig}
        
        # Count matches
        match_count = 0
        for col in normalized_cols:
            if col in cleaned_sig:
                match_count += 2  # exact variant match
            else:
                # partial word match
                for s in cleaned_sig:
                    if col in s or s in col:
                        match_count += 1
                        break
        
        score = match_count
        
        # Sheet name bonus
        if sheet_name:
            s_clean = _clean_str(sheet_name)
            for kw in KEYWORD_HINTS.get(t, []):
                if kw in s_clean:
                    score += 8
                    break

        # Filename bonus
        if filename:
            f_clean = _clean_str(filename)
            for kw in KEYWORD_HINTS.get(t, []):
                if kw in f_clean:
                    score += 6
                    break

        scores[t] = score

    total = sum(scores.values())
    if total == 0:
        return {"detected_type": None, "confidence": 0.0, "scores": scores}

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return {"detected_type": None, "confidence": 0.0, "scores": scores}

    # Sort scores to see margin between #1 and #2
    sorted_scores = sorted(scores.values(), reverse=True)
    second_best = sorted_scores[1] if len(sorted_scores) > 1 else 0

    if best_score == second_best and best_score > 0:
        # Tie
        confidence = 0.5
    else:
        # Confidence based on score strength and margin over runner-up
        margin = (best_score - second_best) / max(1, best_score)
        confidence = round(min(1.0, 0.6 + (0.4 * margin)), 4)

    return {"detected_type": best_type, "confidence": confidence, "scores": scores}
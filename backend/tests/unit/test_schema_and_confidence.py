from app.excel.schema_detector import detect_import_type
from app.excel.confidence_matcher import compute_match_confidence, find_best_match


def test_detect_student_columns():
    result = detect_import_type(["Roll No", "Name", "Email", "Department", "Batch", "Group"])
    assert result["detected_type"] == "student"
    assert result["confidence"] > 0.7


def test_detect_department_columns():
    result = detect_import_type(["Code", "Name"])
    assert result["detected_type"] == "department"


def test_detect_returns_none_for_unrecognized_columns():
    result = detect_import_type(["Foo", "Bar", "Baz"])
    assert result["detected_type"] is None
    assert result["confidence"] == 0.0


def test_detect_handles_empty_column_list():
    result = detect_import_type([])
    assert result["detected_type"] is None


def test_compute_match_confidence_exact_match_case_insensitive():
    assert compute_match_confidence("CSE", "cse") == 1.0


def test_compute_match_confidence_whitespace_trimmed():
    assert compute_match_confidence("  CSE  ", "CSE") == 1.0


def test_compute_match_confidence_partial_match():
    score = compute_match_confidence("Comp Sci", "Computer Science")
    assert 0.0 < score < 1.0


def test_compute_match_confidence_empty_values():
    assert compute_match_confidence("", "CSE") == 0.0
    assert compute_match_confidence("CSE", "") == 0.0


def test_find_best_match_returns_matched_above_threshold():
    candidates = [{"code": "CSE"}, {"code": "ECE"}, {"code": "MECH"}]
    result = find_best_match("cse", candidates, "code", threshold=0.6)
    assert result["matched"] is True
    assert result["best_candidate"]["code"] == "CSE"
    assert result["confidence"] == 1.0


def test_find_best_match_returns_unmatched_below_threshold():
    candidates = [{"code": "CSE"}, {"code": "ECE"}]
    result = find_best_match("ZZZZZ", candidates, "code", threshold=0.6)
    assert result["matched"] is False
    assert result["best_candidate"] is None


def test_find_best_match_handles_no_candidates():
    result = find_best_match("CSE", [], "code")
    assert result["matched"] is False
    assert result["confidence"] == 0.0

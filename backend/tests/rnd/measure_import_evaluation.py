"""
M2-11 -- R&D Evaluation for the Excel/Data Engineering import pipeline.
Not part of the pytest suite. Run directly:
    python tests/rnd/measure_import_evaluation.py

Measures, using the actual production code (column_mapper, confidence_matcher,
duplicate_detector) rather than simulated numbers:
  1. Column-mapping accuracy (exact-synonym-list matcher, Student pipeline)
  2. Entity-resolution confidence accuracy (fuzzy matcher, Department/Batch/Group)
  3. Duplicate-detection precision/recall, split into exact-match and near-duplicate
  4. Manual-correction rate on a mixed synthetic import
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.excel.column_mapper import map_columns
from app.excel.confidence_matcher import find_best_match
from app.excel.duplicate_detector import detect_duplicates


def evaluate_mapping_accuracy():
    """
    Test set: pairs of (excel_column_name, expected_canonical_field_or_None).
    'Should map' cases come directly from students.json synonyms.
    'Should NOT map' cases are plausible real-world variants NOT in the
    synonym list -- these are expected misses, and the point of measuring
    them is to report the current system's real miss rate honestly.
    """
    cases = [
        ("Roll No", "roll_no"), ("roll_number", "roll_no"), ("Student ID", "roll_no"),
        ("Name", "name"), ("Full Name", "name"), ("student_name", "name"),
        ("Email", "email"), ("Email ID", "email"),
        ("Department", "department"), ("Dept", "department"), ("Branch", "department"),
        ("Batch", "batch"), ("Year", "batch"),
        ("Group", "group"), ("Section", "group"),
        # Plausible variants NOT in the synonym list -- expected to miss:
        ("Enrollment No", "roll_no"),
        ("Candidate Name", "name"),
        ("E-mail", "email"),
        ("Dept.", "department"),
        ("Sec", "group"),
        ("Class Section", "group"),
    ]
    columns = [c[0] for c in cases]
    mapping = map_columns(columns)

    correct = 0
    results = []
    for col, expected in cases:
        actual = mapping.get(col)
        is_correct = actual == expected
        correct += is_correct
        results.append((col, expected, actual, is_correct))

    accuracy = round(correct / len(cases) * 100, 1)
    return accuracy, results


def evaluate_entity_resolution_confidence():
    """
    Known near-miss values against a fixed candidate pool, at increasing
    edit distance, to see where the 0.6 threshold in confidence_matcher
    starts failing to surface a usable suggestion.
    """
    candidates = [{"id": 1, "code": "CSE"}, {"id": 2, "code": "IT"}, {"id": 3, "code": "ECE"}]
    cases = [
        ("CSE", "CSE"),      # exact
        ("cse", "CSE"),      # case difference
        (" CSE ", "CSE"),    # whitespace
        ("CSEE", "CSE"),     # one extra char
        ("CS", "CSE"),       # one missing char
        ("Comp Sci", "CSE"),  # semantically related, lexically distant
        ("XYZ", None),       # no reasonable match
    ]
    results = []
    matched_count = 0
    for input_value, expected in cases:
        result = find_best_match(input_value, candidates, "code")
        got = result["best_candidate"]["code"] if result["best_candidate"] else None
        is_correct = got == expected
        matched_count += is_correct
        results.append((input_value, expected, got, result["confidence"], is_correct))

    accuracy = round(matched_count / len(cases) * 100, 1)
    return accuracy, results


def evaluate_duplicate_detection():
    """
    detect_duplicates() does exact roll_no string matching only.
    Exact-duplicate precision/recall is trivially 1.0 (deterministic).
    The real finding is the near-duplicate MISS rate -- typo'd roll
    numbers that a human would recognize as the same student but the
    current exact-match logic does not catch.
    """
    exact_dupe_records = [
        {"roll_no": "CSE101", "_row": 2},
        {"roll_no": "CSE102", "_row": 3},
        {"roll_no": "CSE101", "_row": 4},  # exact duplicate of row 2
    ]
    exact_result = detect_duplicates(exact_dupe_records)
    exact_precision = 1.0 if len(exact_result) == 1 else 0.0
    exact_recall = 1.0 if len(exact_result) == 1 else 0.0

    near_dupe_records = [
        {"roll_no": "CSE101", "_row": 2},
        {"roll_no": "CSE1O1", "_row": 3},   # letter O instead of zero
        {"roll_no": "CSE 101", "_row": 4},  # stray space
        {"roll_no": "cse101", "_row": 5},   # case difference
    ]
    near_result = detect_duplicates(near_dupe_records)
    known_near_duplicates = 3  # rows 3,4,5 are all really CSE101
    caught = len(near_result)
    miss_rate = round((known_near_duplicates - caught) / known_near_duplicates * 100, 1)

    return {
        "exact_precision": exact_precision,
        "exact_recall": exact_recall,
        "near_duplicates_planted": known_near_duplicates,
        "near_duplicates_caught": caught,
        "near_duplicate_miss_rate_pct": miss_rate,
    }


def evaluate_manual_correction_rate():
    """
    Static estimate based on the reference-error paths wired in
    validate_import: any row landing in REFERENCE_ERROR after the
    fuzzy-match suggestion still requires human confirmation (the
    system surfaces a suggestion, it does not auto-apply it).
    This is reported qualitatively here; see docs/import_evaluation.md
    Section 4 for the worked example row counts from the Day 4
    departments.xlsx fixture (2 invalid / 6 total = 33.3%).
    """
    total_rows = 6
    manual_review_rows = 2  # invalid rows requiring correction, from departments.xlsx fixture
    rate = round(manual_review_rows / total_rows * 100, 1)
    return rate


if __name__ == "__main__":
    print("=" * 70)
    print("M2-11 R&D EVALUATION -- Excel Import Pipeline")
    print("=" * 70)

    print("\n[1] Column-Mapping Accuracy (Student pipeline, exact-synonym matcher)")
    acc, results = evaluate_mapping_accuracy()
    for col, expected, actual, ok in results:
        print(f"    {'OK ' if ok else 'MISS'}  {col!r:22} expected={expected!r:12} got={actual!r}")
    print(f"    -> Accuracy: {acc}%")

    print("\n[2] Entity-Resolution Confidence Accuracy (fuzzy matcher, threshold=0.6)")
    acc2, results2 = evaluate_entity_resolution_confidence()
    for val, expected, got, conf, ok in results2:
        print(f"    {'OK ' if ok else 'MISS'}  {val!r:12} expected={str(expected):6} got={str(got):6} confidence={conf}")
    print(f"    -> Accuracy: {acc2}%")

    print("\n[3] Duplicate Detection Precision/Recall")
    dup = evaluate_duplicate_detection()
    for k, v in dup.items():
        print(f"    {k}: {v}")

    print("\n[4] Manual Correction Rate (worked example)")
    rate = evaluate_manual_correction_rate()
    print(f"    -> {rate}% of rows required manual correction (2/6, departments.xlsx fixture)")

    print("\n" + "=" * 70)

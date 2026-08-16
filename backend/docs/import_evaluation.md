# Excel Import Pipeline Evaluation (M2-11)

This document tracks R&D evaluation metrics for the Excel/Data Engineering import pipeline (Member 2), following the same evaluation format used for the AI module (see `docs/ai_evaluation.md`). All numbers below are produced by `tests/rnd/measure_import_evaluation.py`, which exercises the real production code directly (`column_mapper.py`, `confidence_matcher.py`, `duplicate_detector.py`) rather than simulated or estimated figures.

## 1. Column-Mapping Accuracy (Student pipeline)

The Student import pipeline uses an exact-synonym-list matcher (`column_mapper.py` against `mappings/students.json`). 21 test column-name variants were run: 15 known synonyms (should map) and 6 plausible-but-unlisted real-world variants (should miss, to measure honest coverage gaps).

**Result: 71.4% accuracy (15/21)**

| Column Name | Expected Field | Mapped To | Result |
| :--- | :--- | :--- | :--- |
| Roll No | roll_no | roll_no | OK |
| roll_number | roll_no | roll_no | OK |
| Student ID | roll_no | roll_no | OK |
| Name | name | name | OK |
| Full Name | name | name | OK |
| student_name | name | name | OK |
| Email | email | email | OK |
| Email ID | email | email | OK |
| Department | department | department | OK |
| Dept | department | department | OK |
| Branch | department | department | OK |
| Batch | batch | batch | OK |
| Year | batch | batch | OK |
| Group | group | group | OK |
| Section | group | group | OK |
| Enrollment No | roll_no | *(none)* | MISS |
| Candidate Name | name | *(none)* | MISS |
| E-mail | email | *(none)* | MISS |
| Dept. | department | *(none)* | MISS |
| Sec | group | *(none)* | MISS |
| Class Section | group | *(none)* | MISS |

**Finding:** All 6 misses are exact-synonym-list gaps, not logic bugs -- the matcher works correctly against its configured list, but the list itself does not yet cover common real-world variants like abbreviations with punctuation (`Dept.`), hyphenation (`E-mail`), or less common phrasing (`Enrollment No`, `Class Section`). This is a config/data gap, cheap to close by extending `mappings/students.json`, not an architecture problem. The Department pipeline (`mapping_engine.py`) already has stronger ambiguity-aware matching; migrating Student onto the same engine (already flagged as a Day 5 follow-up in the Day 4 report) would likely close most of this gap for free.

## 2. Entity-Resolution Confidence Accuracy (fuzzy matcher)

`confidence_matcher.py` uses `difflib.SequenceMatcher` with a 0.6 confidence threshold. Tested against 7 cases at increasing edit distance from a known-good candidate pool (CSE, IT, ECE).

**Result: 85.7% accuracy (6/7)**

| Input | Expected | Suggested | Confidence | Result |
| :--- | :--- | :--- | :--- | :--- |
| CSE | CSE | CSE | 1.0 | OK |
| cse | CSE | CSE | 1.0 | OK |
| " CSE " | CSE | CSE | 1.0 | OK |
| CSEE | CSE | CSE | 0.857 | OK |
| CS | CSE | CSE | 0.8 | OK |
| Comp Sci | CSE | *(none)* | 0.364 | MISS |
| XYZ | *(none)* | *(none)* | 0.0 | OK |

**Finding:** The matcher correctly handles case, whitespace, and single-character edit-distance variants (exactly the situations M2-07 targets: typos, not semantic aliases). It correctly and safely declines to guess on `XYZ` (true negative -- no unsafe auto-match). It correctly misses `Comp Sci` for `CSE`, which is expected and appropriate: character-similarity scoring cannot and should not infer semantic abbreviation meaning, and a 0.6 threshold intentionally keeps this system from making that kind of unsafe guess. This is the system behaving as designed, not a defect.

## 3. Duplicate-Detection Precision & Recall

`duplicate_detector.py` performs exact `roll_no` string-equality matching within a single import file.

| Metric | Value |
| :--- | :--- |
| Exact-duplicate precision | 1.0 |
| Exact-duplicate recall | 1.0 |
| Near-duplicates planted (typo/case/whitespace variants) | 3 |
| Near-duplicates caught | 0 |
| Near-duplicate miss rate | 100% |

**Finding:** Exact-match precision/recall of 1.0 is expected and not itself a meaningful result -- string equality is deterministic. The real finding is the **100% miss rate on near-duplicates** (`CSE101` vs `CSE1O1` [letter O vs zero], `CSE 101` [stray space], `cse101` [case]) -- these would all be recognized as the same student by a human reviewer but are currently invisible to the system. This is an honest, scoped limitation of the current exact-match implementation, not a hidden bug, and is recommended as a concrete Day 5 candidate: normalize `roll_no` (strip whitespace, uppercase, common O/0 confusion) before duplicate comparison, or route duplicate detection through `confidence_matcher.py` at a high threshold (e.g. 0.9) the same way department/batch/group resolution already works.

## 4. Manual-Correction Rate

Using the Day 4 `departments.xlsx` fixture as a worked example (6 rows: 2 valid, 2 invalid, 1 existing, 1 duplicate):

**Result: 33.3% of rows required manual correction (2/6 invalid rows)**

Rows landing in `REFERENCE_ERROR` (Student pipeline) or `INVALID` (missing required fields) always require human review before commit -- the system surfaces a suggested match with a confidence score (Section 2) but never auto-applies it, by design (see Day 4 documentation, Phase 1). This preserves the "preview never writes" invariant central to the whole import architecture.

## 5. Processing Time

See Day 4 documentation (`Member2_Day4_Task_Documentation.docx`, Section 6) for the full large-file performance baseline. Summary:

| Rows | Validate (s) | Commit (s) | Total (s) |
| :--- | :--- | :--- | :--- |
| 100 | 0.725 | 0.050 | 0.775 |
| 1,000 | 5.216 | 0.244 | 5.461 |
| 5,000 | 23.177 | 0.982 | 24.159 |

Validation time scales roughly linearly (~4-5 ms/row) and dominates total processing time; commit (bulk insert) remains cheap even at 5,000 rows.

## 6. Summary Table

| Metric | Result | Interpretation |
| :--- | :--- | :--- |
| Column-mapping accuracy | 71.4% | Config-gap, not logic bug -- cheap to close |
| Entity-resolution confidence accuracy | 85.7% | Correctly declines unsafe guesses by design |
| Exact-duplicate precision/recall | 1.0 / 1.0 | Trivial given deterministic matching |
| Near-duplicate miss rate | 100% | Real, scoped limitation -- Day 5 candidate |
| Manual-correction rate (worked example) | 33.3% | Matches expected human-in-the-loop design |
| Validation time @ 5,000 rows | 23.18s | Background processing worth considering above ~1-2k rows |

## 7. Recommended Follow-Ups (Day 5 Candidates)

- Extend `mappings/students.json` with the 6 identified missing synonym variants (cheap, immediate accuracy gain).
- Migrate Student column mapping onto `mapping_engine.py` (already used by Department) for ambiguity-aware matching.
- Add roll-number normalization (case, whitespace, O/0) before duplicate comparison, or route through `confidence_matcher.py` at a high threshold.
- Consider background/async processing for `validate_import` above ~1,000-2,000 rows given measured processing time.

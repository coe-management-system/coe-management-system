import math
import unittest
from datetime import datetime

import pandas as pd

from app.excel.attendance_parser import (
    canonical_status,
    classify_header,
    detect_attendance_format,
    infer_subject_from_filename,
    is_sentinel_reference,
    parse_attendance_date,
    parse_attendance_sheet,
)


def _df(rows, columns):
    df = pd.DataFrame(rows, columns=columns)
    return df.astype(object)


WIDE_COLUMNS = [
    "Serial No.", "Roll No.", "Admission ID", "Student Name", "Branch", "Section",
    "01-Aug-2026", "02-Aug-2026", "03-Aug-2026", "04-Aug-2026", "05-Aug-2026",
]

TX_COLUMNS = ["Addmission No", "Roll No", "Subject", "Date", "Attendance Status"]


class TestCanonicalStatus(unittest.TestCase):

    def test_marks_normalised_case_insensitive(self):
        cases = {
            "P": "PRESENT", "p": "PRESENT", "Present": "PRESENT",
            "A": "ABSENT", "a": "ABSENT", "Absent": "ABSENT",
            "L": "LEAVE", "l": "LEAVE", "Leave": "LEAVE", "OD": "LEAVE",
            "H": "HOLIDAY", "h": "HOLIDAY", "Holiday": "HOLIDAY", "Cancelled": "HOLIDAY",
        }
        for raw, expected in cases.items():
            status, reason = canonical_status(raw)
            self.assertEqual(status, expected, f"raw={raw!r}")

    def test_blank_values_are_blank_not_invalid(self):
        for value in (None, "", "   ", float("nan"), math.nan):
            status, reason = canonical_status(value)
            self.assertIsNone(status, f"value={value!r}")
            self.assertEqual(reason, "blank", f"value={value!r}")

    def test_unknown_words_are_invalid(self):
        for raw in ("x", "u", "?", "-", "??"):
            status, _ = canonical_status(raw)
            self.assertIsNone(status)

    def test_garbage_is_invalid(self):
        status, reason = canonical_status("banana")
        self.assertIsNone(status)
        self.assertIn("invalid attendance mark", reason)


class TestParseDate(unittest.TestCase):

    def test_various_formats(self):
        for raw in (
            "2026-08-01", "2026/08/01", "01-08-2026", "01/08/2026",
            "01-Aug-2026", "01 Aug 2026", "Aug 01 2026", "August 01, 2026",
        ):
            d, err = parse_attendance_date(raw)
            self.assertIsNotNone(d, f"raw={raw!r} err={err!r}")
            self.assertEqual(d.isoformat(), "2026-08-01", f"raw={raw!r}")

    def test_datetime_value(self):
        d, err = parse_attendance_date(datetime(2026, 8, 1, 9, 30))
        self.assertEqual(d.isoformat(), "2026-08-01")
        self.assertEqual(err, "")

    def test_year_less_inferred(self):
        d, err = parse_attendance_date("01-Aug", default_year=2026)
        self.assertEqual(d.isoformat(), "2026-08-01")
        self.assertEqual(err, "year-inferred")

    def test_unparseable_never_coerced_to_today(self):
        from datetime import date as _date
        d, err = parse_attendance_date("not-a-date")
        self.assertIsNone(d)
        self.assertNotEqual(err, "")
        self.assertNotEqual(err, "blank")
        self.assertNotEqual(d, _date.today())

    def test_blank(self):
        d, err = parse_attendance_date(float("nan"))
        self.assertIsNone(d)
        self.assertEqual(err, "blank")


class TestFormatDetection(unittest.TestCase):

    def test_wide_grid_detection(self):
        result = detect_attendance_format(WIDE_COLUMNS)
        self.assertEqual(result["format"], "wide")
        self.assertEqual(result["detected_type"], "attendance")

    def test_transaction_detection(self):
        result = detect_attendance_format(TX_COLUMNS)
        self.assertEqual(result["format"], "transaction")
        self.assertEqual(result["detected_type"], "attendance")

    def test_roster_rejected(self):
        result = detect_attendance_format(
            ["Roll No", "Name", "Email", "Status", "Branch"]
        )
        self.assertEqual(result["format"], None)
        self.assertEqual(result["detected_type"], "roster")

    def test_no_attendance_columns_rejected(self):
        result = detect_attendance_format(["Name", "Phone"])
        self.assertEqual(result["format"], None)
        self.assertEqual(result["detected_type"], "unknown")


class TestSentinel(unittest.TestCase):

    def test_out_of_range(self):
        self.assertTrue(is_sentinel_reference("999999", 100000))
        self.assertTrue(is_sentinel_reference(999999, 100000))
        self.assertTrue(is_sentinel_reference("9999", 100000))
        self.assertFalse(is_sentinel_reference("ECE201", 100000))
        self.assertFalse(is_sentinel_reference("123", 100000))
        self.assertFalse(is_sentinel_reference(None, 100000))


class TestFilenameHint(unittest.TestCase):

    def test_subject_inferred_from_filename(self):
        subject, _branch = infer_subject_from_filename("attendance_ece_math101_g2.xlsx")
        self.assertEqual(subject, "MATH101")

    def test_branch_only_filename(self):
        subject, branch = infer_subject_from_filename("attendance_cse_g1.xlsx")
        self.assertIsNone(subject)
        self.assertEqual(branch, "CSE")


class TestParseWideGrid(unittest.TestCase):

    def test_marks_dates_and_blank_exclusion(self):
        df = _df([
            [1, "CSE101", "ADM1001", "Rahul", "CSE", "G1",
             "P", "p", "A", "H", "", "P"],
        ], WIDE_COLUMNS + ["06-Aug-2026"])
        result = parse_attendance_sheet(df, filename="attendance_cse_g1.xlsx", subject_hint="MATH101")

        self.assertEqual(result["format"], "wide")
        self.assertEqual(result["subject"], "MATH101")
        self.assertEqual(result["subject_source"], "explicit")

        events = result["events"]
        self.assertEqual(len(events), 6)
        self.assertEqual([e["status"] for e in events],
                         ["PRESENT", "PRESENT", "ABSENT", "HOLIDAY", None, "PRESENT"])

        blank_event = events[4]
        self.assertIsNone(blank_event["status"])
        self.assertEqual(blank_event["issues"][0]["type"], "not_marked")

        self.assertTrue(any(i["type"] == "not_marked" for i in result["issues"]))
        self.assertFalse(any(i["type"] == "invalid_mark" for i in result["issues"]))

    def test_duplicate_roll_flagged(self):
        df = _df([
            [1, "CSE101", "ADM1001", "Rahul", "CSE", "G1", "P", "P"],
            [2, "CSE101", "ADM1002", "Priya", "CSE", "G1", "A", "P"],
        ], WIDE_COLUMNS[:6] + ["01-Aug-2026", "02-Aug-2026"])
        result = parse_attendance_sheet(df)
        self.assertTrue(any(i["type"] == "duplicate_student_in_sheet" for i in result["issues"]))
        self.assertTrue(any(e["duplicate_in_sheet"] for e in result["events"]))

    def test_no_subject_flags_required(self):
        df = _df([
            [1, "CSE101", "ADM1001", "Rahul", "CSE", "G1", "P", "P"],
        ], WIDE_COLUMNS[:6] + ["01-Aug-2026", "02-Aug-2026"])
        result = parse_attendance_sheet(df, filename="roster.xlsx")
        self.assertIsNone(result["subject"])
        self.assertTrue(any(i["type"] == "subject_required" for i in result["issues"]))

    def test_invalid_mark_flagged_not_coerced(self):
        df = _df([
            [1, "CSE101", "ADM1001", "Rahul", "CSE", "G1", "banana", "P"],
        ], WIDE_COLUMNS[:6] + ["01-Aug-2026", "02-Aug-2026"])
        result = parse_attendance_sheet(df, subject_hint="MATH101")
        events = result["events"]
        self.assertEqual(events[0]["status"], None)
        self.assertEqual(events[0]["issues"][0]["type"], "invalid_mark")
        self.assertTrue(any(i["type"] == "invalid_mark" for i in result["issues"]))


class TestParseTransactionLog(unittest.TestCase):

    def test_event_rows(self):
        df = _df([
            [1, "ECE201", "SUB101", datetime(2026, 8, 1, 9, 0), "Present"],
            [2, "ECE202", "SUB101", "2026-08-02", "p"],
            [3, "ECE203", "SUB101", "2026/08/03", "Absent"],
        ], TX_COLUMNS)
        result = parse_attendance_sheet(df)
        self.assertEqual(result["format"], "transaction")
        events = result["events"]
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["status"], "PRESENT")
        self.assertEqual(events[0]["date"], "2026-08-01")
        self.assertEqual(events[0]["roll_no"], "ECE201")
        self.assertEqual(events[0]["subject"], "SUB101")

    def test_bad_date_excluded(self):
        df = _df([
            [1, "ECE201", "SUB101", "not-a-date", "P"],
            [2, "ECE202", "SUB101", "2026-08-01", "P"],
        ], TX_COLUMNS)
        result = parse_attendance_sheet(df)
        # The bad-date row is kept for the audit trail but carries no date/status.
        self.assertEqual(len(result["events"]), 2)
        bad = result["events"][0]
        self.assertIsNone(bad["date"])
        self.assertIsNone(bad["status"])
        self.assertEqual(bad["issues"][0]["type"], "bad_date")
        good = result["events"][1]
        self.assertEqual(good["date"], "2026-08-01")
        self.assertEqual(good["status"], "PRESENT")
        self.assertTrue(any(i["type"] == "bad_date" for i in result["issues"]))
        self.assertEqual(result["summary"]["valid_events"], 1)

    def test_sentinel_student_and_subject_flagged(self):
        df = _df([
            [1, "999999", "SUB101", "2026-08-01", "P"],
            [2, "ECE201", "99999", "2026-08-01", "P"],
        ], TX_COLUMNS)
        result = parse_attendance_sheet(df)
        types = [i["type"] for i in result["issues"]]
        self.assertIn("sentinel_student", types)
        self.assertIn("sentinel_subject", types)

    def test_duplicate_event_detected(self):
        df = _df([
            [1, "ECE201", "SUB101", "2026-08-01", "P"],
            [2, "ECE201", "SUB101", "2026-08-01", "A"],
        ], TX_COLUMNS)
        result = parse_attendance_sheet(df)
        self.assertTrue(any(i["type"] == "duplicate_event" for i in result["issues"]))

    def test_missing_student_reference(self):
        df = _df([
            [None, "", "SUB101", "2026-08-01", "P"],
        ], TX_COLUMNS)
        result = parse_attendance_sheet(df)
        self.assertTrue(any(i["type"] == "no_student_reference" for i in result["issues"]))
        self.assertEqual(result["summary"]["valid_events"], 0)


class TestHeaderClassification(unittest.TestCase):

    def test_roll_no_mapped(self):
        self.assertEqual(classify_header("Roll No."), "roll")
        self.assertEqual(classify_header("ADDmission No"), "admission")
        self.assertEqual(classify_header("Attendance Status"), "status")
        self.assertEqual(classify_header("05-Aug-2026"), "date")
        self.assertEqual(classify_header("Date"), "date")
        self.assertEqual(classify_header("Subject Code"), "subject")


if __name__ == "__main__":
    unittest.main()

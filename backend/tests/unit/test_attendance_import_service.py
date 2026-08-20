import os
import tempfile
import unittest
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import openpyxl
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (  # noqa: F401
    Attendance, Batch, Department, Group, ImportJob, Student, Subject,
)
from app.models.user import User
from app.models.role import Role
from app.services.import_service import ImportService
from app.services.attendance_import_service import AttendanceImportService

WIDE = [
    ["Serial No.", "Roll No.", "Admission ID", "Student Name", "Branch", "Section",
     "01-Aug-2026", "02-Aug-2026", "03-Aug-2026", "04-Aug-2026", "05-Aug-2026"],
    [1, "CSE101", "ADM1001", "Rahul Kumar", "CSE", "CSE_G1", "P", "P", "A", "H", ""],
    [2, "CSE102", "ADM1002", "Priya Singh", "CSE", "CSE_G1", "p", "P", "Present", "P", "P"],
    [3, "CSE103", "ADM1003", "Aman Verma", "CSE", "CSE_G1", "A", "A", "A", "L", "P"],
]

TX = [
    ["Addmission No", "Roll No", "Subject", "Date", "Attendance Status"],
    [1, "ECE201", "SUB101", datetime(2026, 8, 1, 9, 0), "Present"],
    [2, "ECE202", "SUB101", "2026-08-01", "p"],
    [3, "999999", "SUB101", "2026-08-01", "P"],
    [4, "ECE201", "SUB101", "not-a-date", "P"],
    [5, "ECE201", "SUB999", "2026-08-02", "P"],
]


def _write_xlsx(rows, path):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)


class AttendanceImportServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    def setUp(self):
        # Fresh copies per test: commit() deletes the uploaded file, so the
        # fixtures must be re-materialised for every test case.
        self.tmp = tempfile.mkdtemp()
        self.wide_path = os.path.join(self.tmp, "attendance_cse_g1.xlsx")
        self.tx_path = os.path.join(self.tmp, "attendance_ece_g2_2026.xlsx")
        _write_xlsx(WIDE, self.wide_path)
        _write_xlsx(TX, self.tx_path)

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.dept = Department(id=1, code="CSE", name="Computer Science")
        self.db.add(self.dept)
        self.batch = Batch(id=1, department_id=1, year=2026, name="Batch 2026")
        self.db.add(self.batch)
        self.group = Group(id=1, batch_id=1, name="CSE_G1")
        self.db.add(self.group)
        self.db.flush()

        self.students = [
            Student(id=1, roll_no="CSE101", admission_id="ADM1001", name="Rahul Kumar",
                    email="r@x.edu", department_id=1, batch_id=1, group_id=1),
            Student(id=2, roll_no="CSE102", admission_id="ADM1002", name="Priya Singh",
                    email="p@x.edu", department_id=1, batch_id=1, group_id=1),
            Student(id=3, roll_no="CSE103", admission_id="ADM1003", name="Aman Verma",
                    email="a@x.edu", department_id=1, batch_id=1, group_id=1),
            Student(id=4, roll_no="ECE201", admission_id="ADM2001", name="Kiran Rao",
                    email="k@x.edu", department_id=1, batch_id=1, group_id=1),
            Student(id=5, roll_no="ECE202", admission_id="ADM2002", name="Sara Iyer",
                    email="s@x.edu", department_id=1, batch_id=1, group_id=1),
        ]
        self.db.add_all(self.students)
        self.subject = Subject(id=1, code="SUB101", name="Maths", department_id=1)
        self.db.add(self.subject)
        self.db.flush()

        self.role = Role(id=1, name="admin")
        self.user = User(id=1, username="admin", email="admin@x.edu",
                         password_hash="x", role_id=1)
        self.db.add_all([self.role, self.user])
        self.db.commit()

    def _import(self, path, fname, subject_hint=None):
        job = ImportService.create_import(
            self.db, path, fname, self.user.id, "attendance", subject_hint=subject_hint,
        )
        payload = ImportService.validate_attendance_import(self.db, job)
        return job, payload

    def _aggregates(self):
        out = {}
        for s in self.db.scalars(select(Student)).all():
            out[s.roll_no] = (
                s.total_classes_held, s.total_present, s.total_absent, s.attendance_percentage,
            )
        return out

    def test_wide_grid_percentages(self):
        job, payload = self._import(self.wide_path, "attendance_cse_g1.xlsx", subject_hint="SUB101")

        self.assertEqual(payload["format"], "wide")
        self.assertEqual(payload["subject"], "SUB101")
        self.assertEqual(payload["subject_source"], "explicit")

        # CSE101: P P A H (blank) -> blank excluded; 3 held, 2 present -> 66.67%
        # CSE102: p P Present P P -> 5 held, 5 present -> 100%
        # CSE103: A A A L P -> L excluded; 4 held, 1 present -> 25%
        self.assertEqual(payload["summary"]["ready_to_commit"], 14)
        self.assertEqual(payload["summary"]["excluded"], 1)

        result = ImportService.commit_attendance_import(self.db, job)
        self.assertEqual(result["inserted"], 14)
        self.assertEqual(result["excluded_events"], 1)

        agg = self._aggregates()
        self.assertEqual(agg["CSE101"], (3, 2, 1, 66.67))
        self.assertEqual(agg["CSE102"], (5, 5, 0, 100.0))
        self.assertEqual(agg["CSE103"], (4, 1, 3, 25.0))

        # CSE103 below 75% threshold and listed.
        low = result["below_threshold"]
        self.assertTrue(any(r["roll_no"] == "CSE103" for r in low))
        self.assertEqual(result["below_threshold_threshold"], 75.0)

    def test_blank_cell_not_counted_as_absent(self):
        job, payload = self._import(self.wide_path, "attendance_cse_g1.xlsx", subject_hint="SUB101")
        ImportService.commit_attendance_import(self.db, job)
        agg = self._aggregates()
        # CSE101 has a blank on 05-Aug -> total must be 3 (not 4), present 2 (not 2+absent).
        self.assertEqual(agg["CSE101"], (3, 2, 1, 66.67))

    def test_transaction_sentinels_and_bad_date_excluded(self):
        job, payload = self._import(self.tx_path, "attendance_ece_g2_2026.xlsx")

        self.assertEqual(payload["format"], "transaction")
        # 3 real valid events: ECE201(P), ECE202(p), and ECE201 02-Aug is SUB999 -> ref error
        self.assertEqual(payload["summary"]["ready_to_commit"], 2)
        categories = [r["category"] for r in payload["records"]]
        self.assertIn("REFERENCE_ERROR", categories)  # sentinel student 999999
        self.assertIn("REFERENCE_ERROR", categories)  # sentinel subject SUB999
        self.assertIn("EXCLUDED", categories)  # bad date not-a-date

        result = ImportService.commit_attendance_import(self.db, job)
        self.assertEqual(result["inserted"], 2)

        # No placeholder students or subjects were created.
        self.assertEqual(len(self.db.scalars(select(Student)).all()), 5)
        self.assertEqual(len(self.db.scalars(select(Subject)).all()), 1)

        agg = self._aggregates()
        self.assertEqual(agg["ECE201"], (1, 1, 0, 100.0))
        self.assertEqual(agg["ECE202"], (1, 1, 0, 100.0))

    def test_reimport_is_idempotent(self):
        job1, _ = self._import(self.wide_path, "attendance_cse_g1.xlsx", subject_hint="SUB101")
        ImportService.commit_attendance_import(self.db, job1)

        # The upload file is deleted on commit; re-materialise before re-uploading.
        _write_xlsx(WIDE, self.wide_path)
        job2, _ = self._import(self.wide_path, "attendance_cse_g1.xlsx", subject_hint="SUB101")
        result2 = ImportService.commit_attendance_import(self.db, job2)

        # Same data again: nothing double-counted; existing rows are untouched.
        self.assertEqual(result2["inserted"], 0)
        self.assertEqual(result2["updated"], 0)

        agg = self._aggregates()
        self.assertEqual(agg["CSE101"], (3, 2, 1, 66.67))
        self.assertEqual(agg["CSE103"], (4, 1, 3, 25.0))

    def test_overwrite_updates_status(self):
        job1, _ = self._import(self.tx_path, "attendance_ece_g2_2026.xlsx")
        ImportService.commit_attendance_import(self.db, job1)

        # Change one event: ECE201 01-Aug Present -> Absent.
        modified = [list(r) for r in TX]
        modified[1][4] = "Absent"  # ECE201 01-Aug
        path = os.path.join(self.tmp, "attendance_tx_modified.xlsx")
        _write_xlsx(modified, path)

        job2, _ = self._import(path, "attendance_tx_modified.xlsx")
        result2 = ImportService.commit_attendance_import(self.db, job2)
        self.assertEqual(result2["updated"], 1)
        self.assertEqual(len(result2["overwritten"]), 1)
        self.assertEqual(result2["overwritten"][0]["old_status"], "PRESENT")
        self.assertEqual(result2["overwritten"][0]["new_status"], "ABSENT")

        agg = self._aggregates()
        self.assertEqual(agg["ECE201"], (1, 0, 1, 0.0))

    def test_export_contains_updated_rows(self):
        job, _ = self._import(self.wide_path, "attendance_cse_g1.xlsx", subject_hint="SUB101")
        ImportService.commit_attendance_import(self.db, job)

        data = AttendanceImportService.build_export(self.db, job)
        self.assertIsInstance(data, bytes)

        import io
        import openpyxl as ox
        wb = ox.load_workbook(io.BytesIO(data))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], "Roll No")
        codes = [r[0] for r in rows[1:]]
        self.assertIn("CSE101", codes)
        self.assertIn("CSE103", codes)
        # Below-threshold rows carry the status label.
        statuses = {r[0]: r[-1] for r in rows[1:]}
        self.assertEqual(statuses["CSE103"], "Below threshold")
        self.assertEqual(statuses["CSE102"], "OK")

    def test_list_flagged(self):
        job, _ = self._import(self.tx_path, "attendance_ece_g2_2026.xlsx")
        report = AttendanceImportService.list_flagged(self.db, job)
        self.assertEqual(report["import_id"], job.id)
        self.assertGreaterEqual(len(report["flagged_rows"]), 2)


if __name__ == "__main__":
    unittest.main()

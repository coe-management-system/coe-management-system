import unittest
from unittest.mock import MagicMock

from app.models.department import Department
from app.models.subject import Subject
from app.services.subject_service import SubjectService


class TestSubjectService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = SubjectService(self.db)

    def test_create_subject(self):
        department = Department(
            id=1,
            name="Computer Science",
        )

        self.db.get.return_value = department
        self.db.scalar.return_value = None

        result = self.service.create_subject(
            code="CS401",
            name="Cloud Computing",
            department_id=1,
        )

        self.assertIsInstance(
            result,
            Subject,
        )

        self.assertEqual(
            result.code,
            "CS401",
        )

        self.assertEqual(
            result.name,
            "Cloud Computing",
        )

        self.assertEqual(
            result.department_id,
            1,
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            result,
        )

    def test_create_subject_rejects_missing_department(self):
        self.db.get.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "Department not found",
        ):
            self.service.create_subject(
                code="CS401",
                name="Cloud Computing",
                department_id=999,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_create_subject_rejects_duplicate_code(self):
        department = Department(
            id=1,
            name="Computer Science",
        )

        existing = Subject(
            id=1,
            code="CS401",
            name="Existing Subject",
            department_id=1,
        )

        self.db.get.return_value = department
        self.db.scalar.return_value = existing

        with self.assertRaisesRegex(
            ValueError,
            "Subject code already exists",
        ):
            self.service.create_subject(
                code="CS401",
                name="Cloud Computing",
                department_id=1,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_get_subject(self):
        subject = Subject(
            id=1,
            code="CS401",
            name="Cloud Computing",
            department_id=1,
        )

        self.db.get.return_value = subject

        result = self.service.get_subject(1)

        self.assertIs(result, subject)

        self.db.get.assert_called_once_with(
            Subject,
            1,
        )

    def test_get_missing_subject(self):
        self.db.get.return_value = None

        result = self.service.get_subject(999)

        self.assertIsNone(result)

    def test_update_subject(self):
        subject = Subject(
            id=1,
            code="CS401",
            name="Old Name",
            department_id=1,
        )

        department = Department(
            id=2,
            name="Computer Science",
        )

        self.db.scalar.return_value = None
        self.db.get.return_value = department

        result = self.service.update_subject(
            subject=subject,
            code="CS402",
            name="New Name",
            department_id=2,
        )

        self.assertEqual(
            result.code,
            "CS402",
        )

        self.assertEqual(
            result.name,
            "New Name",
        )

        self.assertEqual(
            result.department_id,
            2,
        )

        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            subject,
        )


if __name__ == "__main__":
    unittest.main()
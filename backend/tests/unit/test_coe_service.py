import unittest
from unittest.mock import MagicMock

from app.models.coe import CoE
from app.models.coe_lab import CoELab
from app.models.company import Company
from app.models.technology import Technology
from app.services.coe_service import CoEService


class TestCoEService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = CoEService(self.db)

    def test_create_coe(self):
        result = self.service.create_coe(
            name="Cloud Computing CoE",
            status="active",
        )

        self.assertIsInstance(result, CoE)
        self.assertEqual(result.name, "Cloud Computing CoE")
        self.assertEqual(result.status, "active")

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_get_coe(self):
        coe = CoE(
            id=1,
            name="Cloud Computing CoE",
            status="active",
        )

        self.db.get.return_value = coe

        result = self.service.get_coe(1)

        self.assertIs(result, coe)
        self.db.get.assert_called_once_with(CoE, 1)

    def test_get_missing_coe(self):
        self.db.get.return_value = None

        result = self.service.get_coe(999)

        self.assertIsNone(result)

    def test_update_coe(self):
        coe = CoE(
            id=1,
            name="Old Name",
            status="inactive",
        )

        result = self.service.update_coe(
            coe=coe,
            name="New Name",
            status="active",
        )

        self.assertEqual(result.name, "New Name")
        self.assertEqual(result.status, "active")

        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(coe)

    def test_create_lab(self):
        coe = CoE(
            id=1,
            name="Cloud Computing CoE",
            status="active",
        )

        self.db.get.return_value = coe

        result = self.service.create_lab(
            coe_id=1,
            name="Cloud Lab",
            location="Block A",
            capacity=30,
        )

        self.assertIsInstance(result, CoELab)
        self.assertEqual(result.coe_id, 1)
        self.assertEqual(result.name, "Cloud Lab")
        self.assertEqual(result.location, "Block A")
        self.assertEqual(result.capacity, 30)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_create_lab_rejects_missing_coe(self):
        self.db.get.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "CoE not found",
        ):
            self.service.create_lab(
                coe_id=999,
                name="Cloud Lab",
                location="Block A",
                capacity=30,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_create_company(self):
        result = self.service.create_company(
            name="Amazon Web Services",
            company_type="Technology",
        )

        self.assertIsInstance(result, Company)
        self.assertEqual(
            result.name,
            "Amazon Web Services",
        )
        self.assertEqual(
            result.type,
            "Technology",
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_get_company(self):
        company = Company(
            id=1,
            name="Amazon Web Services",
            type="Technology",
        )

        self.db.get.return_value = company

        result = self.service.get_company(1)

        self.assertIs(result, company)
        self.db.get.assert_called_once_with(
            Company,
            1,
        )

    def test_update_company(self):
        company = Company(
            id=1,
            name="Old Company",
            type="Technology",
        )

        result = self.service.update_company(
            company=company,
            name="New Company",
            company_type="Cloud",
        )

        self.assertEqual(
            result.name,
            "New Company",
        )
        self.assertEqual(
            result.type,
            "Cloud",
        )

        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            company,
        )

    def test_create_technology(self):
        result = self.service.create_technology(
            name="AWS",
        )

        self.assertIsInstance(
            result,
            Technology,
        )
        self.assertEqual(
            result.name,
            "AWS",
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            result,
        )

    def test_get_technology(self):
        technology = Technology(
            id=1,
            name="AWS",
        )

        self.db.get.return_value = technology

        result = self.service.get_technology(1)

        self.assertIs(result, technology)
        self.db.get.assert_called_once_with(
            Technology,
            1,
        )

    def test_update_technology(self):
        technology = Technology(
            id=1,
            name="Old Technology",
        )

        result = self.service.update_technology(
            technology=technology,
            name="AWS",
        )

        self.assertEqual(
            result.name,
            "AWS",
        )

        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(
            technology,
        )


if __name__ == "__main__":
    unittest.main()
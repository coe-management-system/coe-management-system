from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coe import CoE
from app.models.coe_lab import CoELab
from app.models.company import Company
from app.models.technology import Technology


class CoEService:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # CoE
    # -------------------------

    def create_coe(
        self,
        name: str,
        status: str,
    ) -> CoE:
        coe = CoE(
            name=name,
            status=status,
        )

        self.db.add(coe)
        self.db.commit()
        self.db.refresh(coe)

        return coe

    def get_coe(
        self,
        coe_id: int,
    ) -> CoE | None:
        return self.db.get(CoE, coe_id)

    def get_coes(self) -> list[CoE]:
        return list(
            self.db.scalars(
                select(CoE)
            ).all()
        )

    def update_coe(
        self,
        coe: CoE,
        name: str | None = None,
        status: str | None = None,
    ) -> CoE:
        if name is not None:
            coe.name = name

        if status is not None:
            coe.status = status

        self.db.commit()
        self.db.refresh(coe)

        return coe

    # -------------------------
    # CoE Labs
    # -------------------------

    def create_lab(
        self,
        coe_id: int,
        name: str,
        location: str | None,
        capacity: int | None,
    ) -> CoELab:
        coe = self.db.get(CoE, coe_id)

        if coe is None:
            raise ValueError("CoE not found")

        lab = CoELab(
            coe_id=coe_id,
            name=name,
            location=location,
            capacity=capacity,
        )

        self.db.add(lab)
        self.db.commit()
        self.db.refresh(lab)

        return lab

    def get_lab(
        self,
        lab_id: int,
    ) -> CoELab | None:
        return self.db.get(CoELab, lab_id)

    def get_labs(
        self,
        coe_id: int | None = None,
    ) -> list[CoELab]:
        query = select(CoELab)

        if coe_id is not None:
            query = query.where(
                CoELab.coe_id == coe_id
            )

        return list(
            self.db.scalars(query).all()
        )

    # -------------------------
    # Companies
    # -------------------------

    def create_company(
        self,
        name: str,
        company_type: str | None,
    ) -> Company:
        company = Company(
            name=name,
            type=company_type,
        )

        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)

        return company

    def get_company(
        self,
        company_id: int,
    ) -> Company | None:
        return self.db.get(
            Company,
            company_id,
        )

    def get_companies(self) -> list[Company]:
        return list(
            self.db.scalars(
                select(Company)
            ).all()
        )

    def update_company(
        self,
        company: Company,
        name: str | None = None,
        company_type: str | None = None,
    ) -> Company:
        if name is not None:
            company.name = name

        if company_type is not None:
            company.type = company_type

        self.db.commit()
        self.db.refresh(company)

        return company

    # -------------------------
    # Technologies
    # -------------------------

    def create_technology(
        self,
        name: str,
    ) -> Technology:
        technology = Technology(
            name=name,
        )

        self.db.add(technology)
        self.db.commit()
        self.db.refresh(technology)

        return technology

    def get_technology(
        self,
        technology_id: int,
    ) -> Technology | None:
        return self.db.get(
            Technology,
            technology_id,
        )

    def get_technologies(self) -> list[Technology]:
        return list(
            self.db.scalars(
                select(Technology)
            ).all()
        )

    def update_technology(
        self,
        technology: Technology,
        name: str | None = None,
    ) -> Technology:
        if name is not None:
            technology.name = name

        self.db.commit()
        self.db.refresh(technology)

        return technology
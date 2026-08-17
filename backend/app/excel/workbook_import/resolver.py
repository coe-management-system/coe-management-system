from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.batch import Batch
from app.models.group import Group
from app.models.student import Student

from .planner import (
    BatchPlan,
    DepartmentPlan,
    GroupPlan,
    StudentPlan,
    WorkbookPlan,
)


@dataclass
class DepartmentResolution:
    plan: DepartmentPlan
    existing: Department | None = None


@dataclass
class BatchResolution:
    plan: BatchPlan
    department: Department
    existing: Batch | None = None


@dataclass
class GroupResolution:
    plan: GroupPlan
    department: Department
    batch: Batch | None = None
    existing: Group | None = None


@dataclass
class StudentResolution:
    plan: StudentPlan
    department: Department | None = None
    batch: Batch | None = None
    group: Group | None = None
    existing: Student | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class WorkbookResolution:
    departments: list[DepartmentResolution] = field(default_factory=list)
    batches: list[BatchResolution] = field(default_factory=list)
    groups: list[GroupResolution] = field(default_factory=list)
    students: list[StudentResolution] = field(default_factory=list)

    errors: list[dict] = field(default_factory=list)

    @property
    def new_departments(self) -> list[DepartmentResolution]:
        return [
            item
            for item in self.departments
            if item.existing is None
        ]

    @property
    def new_batches(self) -> list[BatchResolution]:
        return [
            item
            for item in self.batches
            if item.existing is None
        ]

    @property
    def new_groups(self) -> list[GroupResolution]:
        return [
            item
            for item in self.groups
            if item.existing is None
        ]

    @property
    def new_students(self) -> list[StudentResolution]:
        return [
            item
            for item in self.students
            if item.existing is None and not item.errors
        ]

    @property
    def existing_students(self) -> list[StudentResolution]:
        return [
            item
            for item in self.students
            if item.existing is not None
        ]


def _department_lookup(
    db: Session,
    plan: DepartmentPlan,
) -> Department | None:
    """
    Match an existing department by code first, then name.

    This supports both:
        CSE
        Computer Science and Engineering
    """
    code = plan.code.strip()
    name = plan.name.strip()

    if code:
        department = (
            db.query(Department)
            .filter(Department.code == code)
            .first()
        )

        if department:
            return department

    if name:
        return (
            db.query(Department)
            .filter(Department.name == name)
            .first()
        )

    return None


def resolve_departments(
    db: Session,
    plan: WorkbookPlan,
) -> list[DepartmentResolution]:
    resolutions = []

    for department_plan in plan.departments:
        existing = _department_lookup(
            db,
            department_plan,
        )

        resolutions.append(
            DepartmentResolution(
                plan=department_plan,
                existing=existing,
            )
        )

    return resolutions


def resolve_batches(
    db: Session,
    plan: WorkbookPlan,
    departments: list[DepartmentResolution],
) -> list[BatchResolution]:
    """
    Resolve batches using the relationships available in the
    workbook's Groups sheet.

    A batch is not assigned to a department merely because it
    exists in the Batches sheet.
    """
    department_by_source_id = {
        item.plan.source_id: item.existing
        for item in departments
        if item.existing is not None
    }

    resolutions = []

    for group_plan in plan.groups:
        department = department_by_source_id.get(
            group_plan.department_source_id
        )

        if department is None:
            continue

        batch_plan = next(
            (
                batch
                for batch in plan.batches
                if batch.name == group_plan.batch_name
            ),
            None,
        )

        if batch_plan is None:
            continue

        existing = (
            db.query(Batch)
            .filter(
                Batch.department_id == department.id,
                Batch.year == batch_plan.year,
            )
            .first()
        )

        resolutions.append(
            BatchResolution(
                plan=batch_plan,
                department=department,
                existing=existing,
            )
        )

    # Remove duplicate batch resolutions.
    unique = {}

    for resolution in resolutions:
        key = (
            resolution.department.id,
            resolution.plan.name,
        )
        unique[key] = resolution

    return list(unique.values())


def resolve_groups(
    db: Session,
    plan: WorkbookPlan,
    departments: list[DepartmentResolution],
    batches: list[BatchResolution],
) -> list[GroupResolution]:
    department_by_source_id = {
        item.plan.source_id: item.existing
        for item in departments
        if item.existing is not None
    }

    batch_by_key = {
        (
            item.department.id,
            item.plan.name,
        ): item.existing
        for item in batches
    }

    resolutions = []

    for group_plan in plan.groups:
        department = department_by_source_id.get(
            group_plan.department_source_id
        )

        if department is None:
            continue

        batch = batch_by_key.get(
            (
                department.id,
                group_plan.batch_name,
            )
        )

        if batch is None:
            continue

        existing = (
            db.query(Group)
            .filter(
                Group.batch_id == batch.id,
                Group.name == group_plan.name,
            )
            .first()
        )

        resolutions.append(
            GroupResolution(
                plan=group_plan,
                department=department,
                batch=batch,
                existing=existing,
            )
        )

    return resolutions


def resolve_students(
    db: Session,
    plan: WorkbookPlan,
    departments: list[DepartmentResolution],
    batches: list[BatchResolution],
    groups: list[GroupResolution],
) -> list[StudentResolution]:
    department_by_name = {
        item.plan.name.strip().lower(): item.existing
        for item in departments
        if item.existing is not None
    }

    batch_by_key = {
        (
            item.department.id,
            item.plan.name,
        ): item.existing
        for item in batches
        if item.existing is not None
    }

    group_by_key = {
        (
            item.department.id,
            item.batch.id,
            item.plan.name,
        ): item.existing
        for item in groups
        if item.existing is not None
        and item.batch is not None
    }

    resolutions = []

    for student_plan in plan.students:
        errors = []

        department = department_by_name.get(
            student_plan.department_name.strip().lower()
        )

        if department is None:
            errors.append(
                f"Unknown department: "
                f"{student_plan.department_name}"
            )

        batch = None

        if department is not None:
            batch = batch_by_key.get(
                (
                    department.id,
                    str(student_plan.year),
                )
            )

            if batch is None:
                errors.append(
                    f"No batch found for department "
                    f"'{student_plan.department_name}' "
                    f"and year {student_plan.year}"
                )

        group = None

        if department is not None and batch is not None:
            group = group_by_key.get(
                (
                    department.id,
                    batch.id,
                    student_plan.group_name,
                )
            )

            if group is None:
                errors.append(
                    f"No group '{student_plan.group_name}' "
                    f"found for department "
                    f"'{student_plan.department_name}' "
                    f"and year {student_plan.year}"
                )

        existing = (
            db.query(Student)
            .filter(
                Student.roll_no == student_plan.roll_no
            )
            .first()
        )

        resolutions.append(
            StudentResolution(
                plan=student_plan,
                department=department,
                batch=batch,
                group=group,
                existing=existing,
                errors=errors,
            )
        )

    return resolutions


def resolve_workbook(
    db: Session,
    plan: WorkbookPlan,
) -> WorkbookResolution:
    """
    Compare the workbook plan against existing database state.

    IMPORTANT:
    This function is READ ONLY.
    It never creates or modifies database records.
    """
    departments = resolve_departments(db, plan)

    batches = resolve_batches(
        db,
        plan,
        departments,
    )

    groups = resolve_groups(
        db,
        plan,
        departments,
        batches,
    )

    students = resolve_students(
        db,
        plan,
        departments,
        batches,
        groups,
    )

    result = WorkbookResolution(
        departments=departments,
        batches=batches,
        groups=groups,
        students=students,
    )

    for student in students:
        for error in student.errors:
            result.errors.append(
                {
                    "entity": "student",
                    "roll_no": student.plan.roll_no,
                    "error": error,
                }
            )

    return result
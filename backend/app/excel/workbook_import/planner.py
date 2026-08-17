from dataclasses import dataclass, field
from typing import Any


class WorkbookPlanningError(Exception):
    """Raised when workbook relationships cannot be planned safely."""


@dataclass
class DepartmentPlan:
    source_id: str
    name: str
    code: str


@dataclass
class BatchPlan:
    source_id: str
    name: str
    year: int | None = None


@dataclass
class GroupPlan:
    source_id: str
    name: str
    department_source_id: str
    batch_name: str


@dataclass
class StudentPlan:
    roll_no: str
    name: str
    email: str
    department_name: str
    year: int
    group_name: str


@dataclass
class SubjectPlan:
    code: str
    name: str
    department_code: str


@dataclass
class WorkbookPlan:
    departments: list[DepartmentPlan] = field(default_factory=list)
    batches: list[BatchPlan] = field(default_factory=list)
    groups: list[GroupPlan] = field(default_factory=list)
    students: list[StudentPlan] = field(default_factory=list)
    subjects: list[SubjectPlan] = field(default_factory=list)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text


def _parse_int(value: Any, field_name: str) -> int:
    text = _clean(value)
    if not text:
        raise WorkbookPlanningError(f"Missing required numeric value: {field_name}")
    try:
        return int(float(text))
    except (TypeError, ValueError) as exc:
        raise WorkbookPlanningError(f"Invalid numeric value for {field_name}: {text}") from exc


def _get_sheet(workbook: dict, name: str):
    for sheet_name, dataframe in workbook.items():
        if sheet_name.strip().lower() == name.lower():
            return dataframe
    return None


def plan_departments(workbook: dict) -> list[DepartmentPlan]:
    df = _get_sheet(workbook, "Departments")
    if df is None:
        return []
    return [
        DepartmentPlan(
            source_id=_clean(row["Department ID"]),
            name=_clean(row["Department Name"]),
            code=_clean(row["Code"]).upper(),
        )
        for _, row in df.iterrows()
    ]


def plan_batches(workbook: dict) -> list[BatchPlan]:
    df = _get_sheet(workbook, "Batches")
    if df is None:
        return []
    plans = []
    for _, row in df.iterrows():
        name = _clean(row["Batch"])
        year = int(name) if name.isdigit() and len(name) == 4 else None
        plans.append(BatchPlan(source_id=_clean(row["Batch ID"]), name=name, year=year))
    return plans


def plan_groups(workbook: dict) -> list[GroupPlan]:
    df = _get_sheet(workbook, "Groups")
    if df is None:
        return []
    return [
        GroupPlan(
            source_id=_clean(row["Group ID"]),
            name=_clean(row["Group"]),
            department_source_id=_clean(row["Department ID"]),
            batch_name=_clean(row["Batch"]),
        )
        for _, row in df.iterrows()
    ]


def plan_students(workbook: dict) -> list[StudentPlan]:
    df = _get_sheet(workbook, "Students")
    if df is None:
        return []
    plans = []
    for _, row in df.iterrows():
        plans.append(
            StudentPlan(
                roll_no=_clean(row["Admission ID"]).upper(),
                name=_clean(row["Student Name"]),
                email=_clean(row["Email ID"]).lower(),
                department_name=_clean(row["Branch"]),
                year=_parse_int(row["Year"], "Student Year"),
                group_name=_clean(row["Section"]),
            )
        )
    return plans


def plan_subjects(workbook: dict) -> list[SubjectPlan]:
    df = _get_sheet(workbook, "Subjects")
    if df is None:
        return []
    return [
        SubjectPlan(
            code=_clean(row["Subject Code"]).upper(),
            name=_clean(row["Subject Name"]),
            department_code=_clean(row["Department Code"]).upper(),
        )
        for _, row in df.iterrows()
    ]


def build_workbook_plan(workbook: dict) -> WorkbookPlan:
    return WorkbookPlan(
        departments=plan_departments(workbook),
        batches=plan_batches(workbook),
        groups=plan_groups(workbook),
        students=plan_students(workbook),
        subjects=plan_subjects(workbook),
    )

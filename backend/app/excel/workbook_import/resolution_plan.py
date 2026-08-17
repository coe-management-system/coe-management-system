from dataclasses import dataclass, field


@dataclass
class PlannedDepartment:
    source_id: str
    name: str
    code: str
    database_id: int | None = None


@dataclass
class PlannedBatch:
    source_id: str
    name: str
    year: int
    department_source_id: str
    database_id: int | None = None


@dataclass
class PlannedGroup:
    source_id: str
    name: str
    department_source_id: str
    batch_name: str
    database_id: int | None = None


@dataclass
class PlannedStudent:
    roll_no: str
    name: str
    email: str
    department_source_id: str
    year: int
    group_name: str
    database_id: int | None = None


@dataclass
class PlannedSubject:
    code: str
    name: str
    department_source_id: str
    database_id: int | None = None


@dataclass
class WorkbookResolutionPlan:
    departments: list[PlannedDepartment] = field(default_factory=list)
    batches: list[PlannedBatch] = field(default_factory=list)
    groups: list[PlannedGroup] = field(default_factory=list)
    students: list[PlannedStudent] = field(default_factory=list)
    subjects: list[PlannedSubject] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    @property
    def new_departments(self):
        return [item for item in self.departments if item.database_id is None]

    @property
    def new_batches(self):
        return [item for item in self.batches if item.database_id is None]

    @property
    def new_groups(self):
        return [item for item in self.groups if item.database_id is None]

    @property
    def new_students(self):
        return [item for item in self.students if item.database_id is None]

    @property
    def new_subjects(self):
        return [item for item in self.subjects if item.database_id is None]

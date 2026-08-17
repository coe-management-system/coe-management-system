from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.department import Department
from app.models.group import Group
from app.models.student import Student
from app.models.subject import Subject

from .planner import WorkbookPlan
from .resolution_plan import (
    PlannedBatch,
    PlannedDepartment,
    PlannedGroup,
    PlannedStudent,
    PlannedSubject,
    WorkbookResolutionPlan,
)


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _append_duplicate_errors(
    items,
    key_fn,
    entity: str,
    field: str,
    errors: list[dict],
) -> None:
    seen: dict[str, int] = {}

    for index, item in enumerate(items, start=2):
        key = _clean(key_fn(item)).casefold()

        if not key:
            continue

        if key in seen:
            errors.append(
                {
                    "entity": entity,
                    "row": index,
                    "field": field,
                    "value": key_fn(item),
                    "error": (
                        f"Duplicate {field} in workbook; "
                        f"first occurrence is row {seen[key]}"
                    ),
                }
            )
        else:
            seen[key] = index


def _find_department(
    db: Session,
    name: str,
    code: str,
):
    code = _clean(code).upper()
    name = _clean(name)

    if code:
        department = (
            db.query(Department)
            .filter(Department.code == code)
            .first()
        )

        if department:
            return department

    if name:
        department = (
            db.query(Department)
            .filter(Department.name == name)
            .first()
        )

        if department:
            return department

    return None


def build_department_resolution(
    db: Session,
    workbook_plan: WorkbookPlan,
):
    departments: list[PlannedDepartment] = []
    lookup: dict[str, PlannedDepartment] = {}
    errors: list[dict] = []

    _append_duplicate_errors(
        workbook_plan.departments,
        lambda x: x.source_id,
        "department",
        "Department ID",
        errors,
    )

    _append_duplicate_errors(
        workbook_plan.departments,
        lambda x: x.code,
        "department",
        "Code",
        errors,
    )

    _append_duplicate_errors(
        workbook_plan.departments,
        lambda x: x.name,
        "department",
        "Department Name",
        errors,
    )

    for item in workbook_plan.departments:
        if not item.source_id or not item.name or not item.code:
            errors.append(
                {
                    "entity": "department",
                    "source_id": item.source_id,
                    "error": (
                        "Department ID, Department Name "
                        "and Code are required"
                    ),
                }
            )
            continue

        existing = _find_department(
            db,
            item.name,
            item.code,
        )

        planned = PlannedDepartment(
            source_id=item.source_id,
            name=item.name,
            code=item.code,
            database_id=existing.id if existing else None,
        )

        departments.append(planned)
        lookup[item.source_id] = planned

    return departments, lookup, errors


def build_batch_resolution(
    db: Session,
    workbook_plan: WorkbookPlan,
    departments: dict[str, PlannedDepartment],
):
    batch_names_by_department: dict[str, set[str]] = {}
    errors: list[dict] = []

    for group in workbook_plan.groups:
        department_source_id = _clean(
            group.department_source_id
        )
        batch_name = _clean(group.batch_name)

        if not department_source_id or not batch_name:
            errors.append(
                {
                    "entity": "group",
                    "source_id": group.source_id,
                    "error": (
                        "Department ID and Batch are required "
                        "for a group"
                    ),
                }
            )
            continue

        batch_names_by_department.setdefault(
            department_source_id,
            set(),
        ).add(batch_name)

    batch_lookup_by_name = {
        _clean(batch.name): batch
        for batch in workbook_plan.batches
    }

    batches: list[PlannedBatch] = []
    lookup: dict[tuple[str, str], PlannedBatch] = {}

    _append_duplicate_errors(
        workbook_plan.batches,
        lambda x: x.source_id,
        "batch",
        "Batch ID",
        errors,
    )

    _append_duplicate_errors(
        workbook_plan.batches,
        lambda x: x.name,
        "batch",
        "Batch",
        errors,
    )

    for department_source_id, batch_names in (
        batch_names_by_department.items()
    ):
        department = departments.get(department_source_id)

        if department is None:
            errors.append(
                {
                    "entity": "batch",
                    "department_source_id": department_source_id,
                    "error": (
                        "Batch references an unknown "
                        "Department ID"
                    ),
                }
            )
            continue

        for batch_name in sorted(batch_names):
            source_batch = batch_lookup_by_name.get(batch_name)

            if source_batch is None:
                errors.append(
                    {
                        "entity": "batch",
                        "department_source_id": department_source_id,
                        "batch": batch_name,
                        "error": (
                            "Group references a batch that is "
                            "missing from the Batches sheet"
                        ),
                    }
                )
                continue

            if (
                source_batch.year is None
                and not source_batch.source_id.startswith("auto:")
            ):
                errors.append(
                    {
                        "entity": "batch",
                        "source_id": source_batch.source_id,
                        "error": (
                            f"Batch '{source_batch.name}' "
                            "must be a four-digit year"
                        ),
                    }
                )
                continue

            existing = None

            if department.database_id is not None:
                existing = (
                    db.query(Batch)
                    .filter(
                        Batch.department_id
                        == department.database_id,
                        Batch.year == source_batch.year,
                    )
                    .first()
                )

            planned = PlannedBatch(
                source_id=source_batch.source_id,
                name=source_batch.name,
                year=source_batch.year,
                department_source_id=department_source_id,
                database_id=(
                    existing.id
                    if existing
                    else None
                ),
            )

            lookup[
                (
                    department_source_id,
                    batch_name,
                )
            ] = planned

            batches.append(planned)

    return batches, lookup, errors


def build_group_resolution(
    db: Session,
    workbook_plan: WorkbookPlan,
    departments: dict[str, PlannedDepartment],
    batches: dict[tuple[str, str], PlannedBatch],
):
    groups: list[PlannedGroup] = []
    lookup: dict[
        tuple[str, str, str],
        PlannedGroup,
    ] = {}
    errors: list[dict] = []

    for item in workbook_plan.groups:
        department_source_id = _clean(
            item.department_source_id
        )
        batch_name = _clean(item.batch_name)
        group_name = _clean(item.name)

        department = departments.get(
            department_source_id
        )

        if department is None:
            errors.append(
                {
                    "entity": "group",
                    "source_id": item.source_id,
                    "error": (
                        "Unknown department source ID: "
                        f"{department_source_id}"
                    ),
                }
            )
            continue

        batch = batches.get(
            (
                department_source_id,
                batch_name,
            )
        )

        if batch is None:
            errors.append(
                {
                    "entity": "group",
                    "source_id": item.source_id,
                    "error": (
                        f"Unknown batch '{batch_name}' "
                        f"for department '{department.name}'"
                    ),
                }
            )
            continue

        if not group_name:
            errors.append(
                {
                    "entity": "group",
                    "source_id": item.source_id,
                    "error": "Group name is required",
                }
            )
            continue

        existing = None

        if batch.database_id is not None:
            existing = (
                db.query(Group)
                .filter(
                    Group.batch_id == batch.database_id,
                    Group.name == group_name,
                )
                .first()
            )

        key = (
            department_source_id,
            batch_name,
            group_name,
        )

        if key in lookup:
            errors.append(
                {
                    "entity": "group",
                    "source_id": item.source_id,
                    "error": (
                        f"Duplicate group '{group_name}' "
                        f"for batch '{batch_name}'"
                    ),
                }
            )
            continue

        planned = PlannedGroup(
            source_id=item.source_id,
            name=group_name,
            department_source_id=department_source_id,
            batch_name=batch_name,
            database_id=(
                existing.id
                if existing
                else None
            ),
        )

        lookup[key] = planned
        groups.append(planned)

    return groups, lookup, errors


def ensure_student_database_hierarchy(
    db: Session,
    workbook_plan: WorkbookPlan,
    departments: list[PlannedDepartment],
    department_lookup: dict[str, PlannedDepartment],
    batches: list[PlannedBatch],
    batch_lookup: dict[tuple[str, str], PlannedBatch],
    groups: list[PlannedGroup],
    group_lookup: dict[tuple[str, str, str], PlannedGroup],
):
    """
    Resolve Department -> Batch -> Group for students.

    If an entity already exists in the database, its database_id
    is recorded.

    If an entity does not exist, it is represented as a new planned
    entity with database_id=None.

    No database records are created here.
    """

    errors: list[dict] = []

    department_by_name = {
        _clean(item.name).casefold(): item
        for item in department_lookup.values()
    }

    department_by_code = {
        _clean(item.code).upper(): item
        for item in department_lookup.values()
    }

    db_department_cache: dict[
        str,
        PlannedDepartment,
    ] = {}

    db_batch_cache: dict[
        tuple[int, int],
        PlannedBatch,
    ] = {}

    db_group_cache: dict[
        tuple[int, str],
        PlannedGroup,
    ] = {}

    for item in workbook_plan.students:
        department_name = _clean(
            item.department_name
        )

        if not department_name:
            continue

        # ---------------------------------------------------------
        # 1. Resolve or create planned Department
        # ---------------------------------------------------------

        department = (
            department_by_name.get(
                department_name.casefold()
            )
            or department_by_code.get(
                department_name.upper()
            )
        )

        if department is None:
            cache_key = department_name.casefold()

            department = db_department_cache.get(
                cache_key
            )

            if department is None:
                existing_department = _find_department(
                    db,
                    department_name,
                    department_name,
                )

                if existing_department is not None:
                    department = PlannedDepartment(
                        source_id=(
                            f"db:{existing_department.id}"
                        ),
                        name=existing_department.name,
                        code=existing_department.code,
                        database_id=existing_department.id,
                    )
                else:
                    # New department discovered from the
                    # Students sheet.
                    department = PlannedDepartment(
                        source_id=(
                            f"auto:department:"
                            f"{department_name}"
                        ),
                        name=department_name,
                        code=department_name.upper(),
                        database_id=None,
                    )

                db_department_cache[
                    cache_key
                ] = department

                department_lookup[
                    department.source_id
                ] = department

                department_by_name[
                    _clean(
                        department.name
                    ).casefold()
                ] = department

                department_by_code[
                    _clean(
                        department.code
                    ).upper()
                ] = department

                departments.append(department)

        # ---------------------------------------------------------
        # 2. Resolve or create planned Batch
        # ---------------------------------------------------------

        batch_name = str(item.year)

        batch_key = (
            department.source_id,
            batch_name,
        )

        batch = batch_lookup.get(batch_key)

        if batch is None and department.database_id is not None:
            db_batch_key = (
                department.database_id,
                int(item.year),
            )

            batch = db_batch_cache.get(
                db_batch_key
            )

            if batch is None:
                existing_batch = (
                    db.query(Batch)
                    .filter(
                        Batch.department_id
                        == department.database_id,
                        Batch.year == int(item.year),
                    )
                    .first()
                )

                if existing_batch is not None:
                    batch = PlannedBatch(
                        source_id=(
                            f"db:{existing_batch.id}"
                        ),
                        name=str(existing_batch.year),
                        year=existing_batch.year,
                        department_source_id=(
                            department.source_id
                        ),
                        database_id=existing_batch.id,
                    )

                    db_batch_cache[
                        db_batch_key
                    ] = batch

        # If the batch does not exist in the database,
        # create a planned batch. It will be persisted only
        # during commit.
        if batch is None:
            batch = PlannedBatch(
                source_id=(
                    f"auto:batch:"
                    f"{department.source_id}:"
                    f"{batch_name}"
                ),
                name=batch_name,
                year=int(item.year),
                department_source_id=(
                    department.source_id
                ),
                database_id=None,
            )

        batch_lookup[batch_key] = batch

        if batch not in batches:
            batches.append(batch)

        # ---------------------------------------------------------
        # 3. Resolve or create planned Group
        # ---------------------------------------------------------

        group_name = _clean(
            item.group_name
        )

        if not group_name:
            continue

        group_key = (
            department.source_id,
            batch_name,
            group_name,
        )

        group = group_lookup.get(group_key)

        if group is None and batch.database_id is not None:
            db_group_key = (
                batch.database_id,
                group_name.casefold(),
            )

            group = db_group_cache.get(
                db_group_key
            )

            if group is None:
                existing_group = (
                    db.query(Group)
                    .filter(
                        Group.batch_id
                        == batch.database_id,
                        Group.name
                        == group_name,
                    )
                    .first()
                )

                if existing_group is not None:
                    group = PlannedGroup(
                        source_id=(
                            f"db:{existing_group.id}"
                        ),
                        name=existing_group.name,
                        department_source_id=(
                            department.source_id
                        ),
                        batch_name=batch_name,
                        database_id=existing_group.id,
                    )

                    db_group_cache[
                        db_group_key
                    ] = group

        # If the group doesn't exist in the database,
        # represent it as a new planned group.
        if group is None:
            group = PlannedGroup(
                source_id=(
                    f"auto:group:"
                    f"{department.source_id}:"
                    f"{batch_name}:"
                    f"{group_name}"
                ),
                name=group_name,
                department_source_id=(
                    department.source_id
                ),
                batch_name=batch_name,
                database_id=None,
            )

        group_lookup[group_key] = group

        if group not in groups:
            groups.append(group)

    return errors


def build_student_resolution(
    db: Session,
    workbook_plan: WorkbookPlan,
    departments: dict[str, PlannedDepartment],
    batches: dict[tuple[str, str], PlannedBatch],
    groups: dict[
        tuple[str, str, str],
        PlannedGroup,
    ],
):
    students: list[PlannedStudent] = []
    errors: list[dict] = []

    department_by_name = {
        _clean(item.name).casefold(): item
        for item in departments.values()
    }

    department_by_code = {
        _clean(item.code).upper(): item
        for item in departments.values()
    }

    _append_duplicate_errors(
        workbook_plan.students,
        lambda x: x.roll_no,
        "student",
        "Admission ID",
        errors,
    )

    _append_duplicate_errors(
        workbook_plan.students,
        lambda x: x.email,
        "student",
        "Email ID",
        errors,
    )

    for item in workbook_plan.students:
        if (
            not item.roll_no
            or not item.name
            or not item.email
        ):
            errors.append(
                {
                    "entity": "student",
                    "roll_no": item.roll_no,
                    "error": (
                        "Admission ID, Student Name "
                        "and Email ID are required"
                    ),
                }
            )
            continue

        department_name = _clean(
            item.department_name
        )

        department = (
            department_by_name.get(
                department_name.casefold()
            )
            or department_by_code.get(
                department_name.upper()
            )
        )

        if department is None:
            errors.append(
                {
                    "entity": "student",
                    "roll_no": item.roll_no,
                    "error": (
                        "Unknown department: "
                        f"{department_name}"
                    ),
                }
            )
            continue

        batch = batches.get(
            (
                department.source_id,
                str(item.year),
            )
        )

        if batch is None:
            errors.append(
                {
                    "entity": "student",
                    "roll_no": item.roll_no,
                    "error": (
                        f"No planned batch for department "
                        f"'{department.name}' and year "
                        f"{item.year}"
                    ),
                }
            )
            continue

        group = groups.get(
            (
                department.source_id,
                str(item.year),
                _clean(item.group_name),
            )
        )

        if group is None:
            errors.append(
                {
                    "entity": "student",
                    "roll_no": item.roll_no,
                    "error": (
                        f"No planned group "
                        f"'{item.group_name}' for "
                        f"department '{department.name}' "
                        f"and year {item.year}"
                    ),
                }
            )
            continue

        existing = (
            db.query(Student)
            .filter(
                Student.roll_no == item.roll_no
            )
            .first()
        )

        if existing is None:
            existing_by_email = (
                db.query(Student)
                .filter(
                    Student.email == item.email
                )
                .first()
            )

            if existing_by_email is not None:
                errors.append(
                    {
                        "entity": "student",
                        "roll_no": item.roll_no,
                        "error": (
                            f"Email '{item.email}' already "
                            f"belongs to student "
                            f"'{existing_by_email.roll_no}'"
                        ),
                    }
                )
                continue

        students.append(
            PlannedStudent(
                roll_no=item.roll_no,
                name=item.name,
                email=item.email,
                department_source_id=(
                    department.source_id
                ),
                year=item.year,
                group_name=item.group_name,
                database_id=(
                    existing.id
                    if existing
                    else None
                ),
            )
        )

    return students, errors


def build_subject_resolution(
    db: Session,
    workbook_plan: WorkbookPlan,
    departments: dict[str, PlannedDepartment],
):
    subjects: list[PlannedSubject] = []
    errors: list[dict] = []

    department_by_code = {
        _clean(item.code).upper(): item
        for item in departments.values()
    }

    _append_duplicate_errors(
        workbook_plan.subjects,
        lambda x: x.code,
        "subject",
        "Subject Code",
        errors,
    )

    for item in workbook_plan.subjects:
        code = _clean(item.code).upper()
        name = _clean(item.name)
        department_code = _clean(
            item.department_code
        ).upper()

        department = department_by_code.get(
            department_code
        )

        if (
            not code
            or not name
            or not department_code
        ):
            errors.append(
                {
                    "entity": "subject",
                    "code": code,
                    "error": (
                        "Subject Code, Subject Name "
                        "and Department Code are required"
                    ),
                }
            )
            continue

        if department is None:
            errors.append(
                {
                    "entity": "subject",
                    "code": code,
                    "error": (
                        "Unknown department code in "
                        f"workbook: {department_code}"
                    ),
                }
            )
            continue

        existing = (
            db.query(Subject)
            .filter(Subject.code == code)
            .first()
        )

        if (
            existing is not None
            and existing.department_id
            != department.database_id
        ):
            errors.append(
                {
                    "entity": "subject",
                    "code": code,
                    "error": (
                        f"Subject code '{code}' already "
                        "belongs to another department"
                    ),
                }
            )
            continue

        subjects.append(
            PlannedSubject(
                code=code,
                name=name,
                department_source_id=(
                    department.source_id
                ),
                database_id=(
                    existing.id
                    if existing
                    else None
                ),
            )
        )

    return subjects, errors


def resolve_master_workbook(
    db: Session,
    workbook_plan: WorkbookPlan,
) -> WorkbookResolutionPlan:
    result = WorkbookResolutionPlan()

    departments, department_lookup, errors = (
        build_department_resolution(
            db,
            workbook_plan,
        )
    )

    result.departments = departments
    result.errors.extend(errors)

    batches, batch_lookup, errors = (
        build_batch_resolution(
            db,
            workbook_plan,
            department_lookup,
        )
    )

    result.batches = batches
    result.errors.extend(errors)

    groups, group_lookup, errors = (
        build_group_resolution(
            db,
            workbook_plan,
            department_lookup,
            batch_lookup,
        )
    )

    result.groups = groups
    result.errors.extend(errors)

    # Student-only workbooks may not contain Departments,
    # Batches or Groups sheets. Resolve those hierarchy
    # records from the existing database and add them to
    # the same resolution plan.
    hierarchy_errors = (
        ensure_student_database_hierarchy(
            db=db,
            workbook_plan=workbook_plan,
            departments=result.departments,
            department_lookup=department_lookup,
            batches=result.batches,
            batch_lookup=batch_lookup,
            groups=result.groups,
            group_lookup=group_lookup,
        )
    )

    result.errors.extend(hierarchy_errors)

    students, errors = build_student_resolution(
        db,
        workbook_plan,
        department_lookup,
        batch_lookup,
        group_lookup,
    )

    result.students = students
    result.errors.extend(errors)

    subjects, errors = build_subject_resolution(
        db,
        workbook_plan,
        department_lookup,
    )

    result.subjects = subjects
    result.errors.extend(errors)

    return result
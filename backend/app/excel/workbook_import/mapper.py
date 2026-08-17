from dataclasses import dataclass
import re
from typing import Any

import pandas as pd

from app.excel.detector import detect_entity


@dataclass(frozen=True)
class SheetDefinition:
    name: str
    required_columns: tuple[str, ...]
    required_sheet: bool = True
    aliases: dict[str, tuple[str, ...]] | None = None


# Canonical workbook names. The master import requires only the core
# hierarchy. Additional sheets are optional and are validated when present.
SHEET_DEFINITIONS = {
    "Departments": SheetDefinition(
        name="Departments",
        required_columns=("Department ID", "Department Name", "Code"),
        aliases={
            "Department ID": ("Department ID", "Department Id", "Dept ID", "Dept Code ID"),
            "Department Name": ("Department Name", "Department", "Dept Name", "Branch Name"),
            "Code": ("Code", "Department Code", "Dept Code", "Branch Code"),
        },
    ),
    "Batches": SheetDefinition(
        name="Batches",
        required_columns=("Batch ID", "Batch"),
        aliases={
            "Batch ID": ("Batch ID", "Batch Id", "Batch Code"),
            "Batch": ("Batch", "Batch Name", "Year", "Academic Year"),
        },
    ),
    "Groups": SheetDefinition(
        name="Groups",
        required_columns=("Group ID", "Group", "Department ID", "Batch"),
        aliases={
            "Group ID": ("Group ID", "Group Id", "Section ID"),
            "Group": ("Group", "Group Name", "Section", "Section Name"),
            "Department ID": ("Department ID", "Department Id", "Dept ID"),
            "Batch": ("Batch", "Batch Name", "Year", "Academic Year"),
        },
    ),
    "Students": SheetDefinition(
        name="Students",
        required_columns=("Admission ID", "Student Name", "Email ID", "Branch", "Year", "Section"),
        aliases={
            "Admission ID": ("Admission ID", "Admission Id", "Admission No", "Admission Number", "Student ID", "Student Id", "Roll No", "Roll Number"),
            "Student Name": ("Student Name", "Name", "Full Name"),
            "Email ID": ("Email ID", "Email", "Email Address", "Email Id"),
            "Branch": ("Branch", "Department", "Department Name", "Dept", "Dept Name"),
            "Year": ("Year", "Batch", "Academic Year", "Batch Year"),
            "Section": ("Section", "Group", "Group Name", "Section Name"),
        },
    ),
    "Subjects": SheetDefinition(
        name="Subjects",
        required_columns=("Subject Code", "Subject Name", "Department Code"),
        required_sheet=False,
        aliases={
            "Subject Code": ("Subject Code", "Subject ID", "Code", "Subject"),
            "Subject Name": ("Subject Name", "Name"),
            "Department Code": ("Department Code", "Dept Code", "Branch Code", "Department"),
        },
    ),
    "Companies": SheetDefinition(
        name="Companies",
        required_columns=("Company ID", "Company Name", "Short Name"),
        required_sheet=False,
        aliases={
            "Company ID": ("Company ID", "Company Id"),
            "Company Name": ("Company Name", "Name"),
            "Short Name": ("Short Name", "Abbreviation", "Code"),
        },
    ),
    "Technologies": SheetDefinition(
        name="Technologies",
        required_columns=("Technology ID", "Technology Name"),
        required_sheet=False,
        aliases={
            "Technology ID": ("Technology ID", "Technology Id"),
            "Technology Name": ("Technology Name", "Name", "Technology"),
        },
    ),
    "Training": SheetDefinition(
        name="Training",
        required_columns=("Training ID", "Program", "Company", "Technology", "Batch", "Group"),
        required_sheet=False,
        aliases={
            "Training ID": ("Training ID", "Training Id"),
            "Program": ("Program", "Training Program", "Training Name"),
            "Company": ("Company", "Company Name", "Vendor"),
            "Technology": ("Technology", "Technology Name"),
            "Batch": ("Batch", "Batch Name", "Year"),
            "Group": ("Group", "Group Name", "Section"),
        },
    ),
    "Attendance": SheetDefinition(
        name="Attendance",
        required_columns=("Admission ID", "Subject Code", "Date", "Attendance Status"),
        required_sheet=False,
        aliases={
            "Admission ID": ("Admission ID", "Admission No", "Student ID", "Roll No"),
            "Subject Code": ("Subject Code", "Subject", "Code"),
            "Date": ("Date", "Attendance Date", "Session Date"),
            "Attendance Status": ("Attendance Status", "Status", "Present/Absent", "Attendance"),
        },
    ),
}


# Entity types produced by the generic detector and their canonical
# workbook sheets consumed by the existing planner.
_ENTITY_TO_SHEET = {
    "student": "Students",
    "department": "Departments",
    "batch": "Batches",
    "group": "Groups",
    "subject": "Subjects",
}

# The generic entity detector uses domain-level canonical field names,
# while the existing workbook planner uses the legacy sheet field names.
# Keep this translation in the mapper so the planner does not need to know
# how the source workbook was structured.
_ENTITY_FIELD_TO_SHEET_FIELD = {
    "student": {
        "roll_no": "Admission ID",
        "name": "Student Name",
        "email": "Email ID",
        "department": "Branch",
        "batch": "Year",
        "group": "Section",
    },
    "department": {
        "name": "Department Name",
        "code": "Code",
    },
    "batch": {
        "name": "Batch",
        "year": "Batch",
        "department": "Department",
    },
    "group": {
        "name": "Group",
        "batch": "Batch",
        "department": "Department ID",
    },
    "subject": {
        "code": "Subject Code",
        "name": "Subject Name",
        "department": "Department Code",
    },
}


class WorkbookMappingError(Exception):
    """Raised when a supported workbook sheet cannot be mapped."""


def _header_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def normalize_sheet_name(name: str) -> str:
    return str(name).strip().lower()


def get_sheet_definition(sheet_name: str) -> SheetDefinition | None:
    normalized = normalize_sheet_name(sheet_name)
    for name, definition in SHEET_DEFINITIONS.items():
        if normalize_sheet_name(name) == normalized:
            return definition
    return None


def _resolve_column_aliases(definition: SheetDefinition, columns: list[str]) -> dict[str, str]:
    by_key = {_header_key(column): column for column in columns}
    aliases = definition.aliases or {}
    rename_map: dict[str, str] = {}

    for canonical in definition.required_columns:
        candidates = aliases.get(canonical, (canonical,))
        source = next((by_key[_header_key(candidate)] for candidate in candidates if _header_key(candidate) in by_key), None)
        if source is not None and source != canonical:
            rename_map[source] = canonical
    return rename_map


def validate_sheet_columns(sheet_name: str, columns: list[str]) -> list[str]:
    definition = get_sheet_definition(sheet_name)
    if definition is None:
        raise WorkbookMappingError(f"Unsupported workbook sheet: {sheet_name}")

    available = {_header_key(column) for column in columns}
    aliases = definition.aliases or {}
    missing = []
    for required in definition.required_columns:
        candidates = aliases.get(required, (required,))
        if not any(_header_key(candidate) in available for candidate in candidates):
            missing.append(required)
    return missing

def _detected_sheet_definition(sheet_name: str, dataframe: Any) -> tuple[SheetDefinition | None, Any, dict[str, Any] | None]:
    """Resolve an unknown sheet from its columns using the generic detector.

    Returns the planner-compatible SheetDefinition, canonicalized DataFrame,
    and detection metadata. A sheet name alone is never used to guess the
    entity here.
    """
    detection = detect_entity(dataframe)
    if detection.entity_type is None:
        return None, dataframe, {
            "entity_type": None,
            "confidence": detection.confidence,
            "ambiguous": detection.ambiguous,
            "reason": detection.reason,
            "matched_fields": detection.matched_fields,
            "unmapped_columns": detection.unmapped_columns,
        }

    canonical_sheet_name = _ENTITY_TO_SHEET.get(detection.entity_type)
    if canonical_sheet_name is None:
        return None, dataframe, {
            "entity_type": detection.entity_type,
            "confidence": detection.confidence,
            "ambiguous": detection.ambiguous,
            "reason": "Detected entity is not supported by the workbook planner",
            "matched_fields": detection.matched_fields,
            "unmapped_columns": detection.unmapped_columns,
        }

    definition = SHEET_DEFINITIONS[canonical_sheet_name]
    field_map = _ENTITY_FIELD_TO_SHEET_FIELD[detection.entity_type]

    # Build source-column -> planner-column mapping from detector output.
    source_to_planner: dict[str, str] = {}
    for entity_field, source_columns in detection.matched_fields.items():
        planner_field = field_map.get(entity_field)
        if planner_field is None:
            continue
        for source_column in source_columns:
            if planner_field in source_to_planner.values():
                # Prefer the first matched source column. This prevents two
                # aliases for the same canonical field from overwriting data.
                continue
            source_to_planner[source_column] = planner_field

    canonical_df = dataframe.copy()
    canonical_df.columns = [str(column).strip() for column in canonical_df.columns]
    canonical_df = canonical_df.rename(columns=source_to_planner)

    # Some planner contracts require synthetic source IDs when the source
    # workbook has no explicit ID column. These IDs are only planning keys;
    # they do not create database records during mapping.
    if canonical_sheet_name == "Departments" and "Department ID" not in canonical_df.columns:
        if "Code" in canonical_df.columns:
            canonical_df["Department ID"] = canonical_df["Code"].map(
                lambda value: f"auto:department:{str(value).strip().upper()}"
            )
        elif "Department Name" in canonical_df.columns:
            canonical_df["Department ID"] = canonical_df["Department Name"].map(
                lambda value: f"auto:department:{str(value).strip()}"
            )

    if canonical_sheet_name == "Batches" and "Batch ID" not in canonical_df.columns:
        if "Batch" in canonical_df.columns:
            canonical_df["Batch ID"] = canonical_df["Batch"].map(
                lambda value: f"auto:batch:{str(value).strip()}"
            )

    if canonical_sheet_name == "Groups" and "Group ID" not in canonical_df.columns:
        if "Group" in canonical_df.columns:
            canonical_df["Group ID"] = canonical_df["Group"].map(
                lambda value: f"auto:group:{str(value).strip()}"
            )

    missing_columns = validate_sheet_columns(canonical_sheet_name, list(canonical_df.columns))
    if missing_columns:
        return definition, canonical_df, {
            "entity_type": detection.entity_type,
            "confidence": detection.confidence,
            "ambiguous": detection.ambiguous,
            "reason": "Detected entity, but required planner fields are missing",
            "matched_fields": detection.matched_fields,
            "unmapped_columns": detection.unmapped_columns,
            "missing_columns": missing_columns,
        }

    return definition, canonical_df, {
        "entity_type": detection.entity_type,
        "confidence": detection.confidence,
        "ambiguous": detection.ambiguous,
        "reason": detection.reason,
        "matched_fields": detection.matched_fields,
        "unmapped_columns": detection.unmapped_columns,
    }

def map_workbook(workbook: dict[str, Any]) -> dict[str, Any]:
    mapped_sheets: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []

    for sheet_name, dataframe in workbook.items():
        # Preserve the existing fast path for canonical sheet names.
        definition = get_sheet_definition(sheet_name)
        detection_metadata = None

        if definition is None:
            definition, dataframe, detection_metadata = _detected_sheet_definition(
                sheet_name,
                dataframe,
            )

            # Unknown/unrelated sheets remain ignorable. A sheet is only an
            # error when the detector has enough evidence to classify it but
            # the resulting entity cannot satisfy the planner contract.
            if definition is None:
                if detection_metadata and detection_metadata.get("entity_type"):
                    errors.append(
                        {
                            "sheet": sheet_name,
                            "error": "ENTITY_DETECTION_FAILED",
                            "entity_type": detection_metadata.get("entity_type"),
                            "confidence": detection_metadata.get("confidence"),
                            "ambiguous": detection_metadata.get("ambiguous"),
                            "message": detection_metadata.get("reason"),
                        }
                    )
                continue
        else:
            columns = [str(column).strip() for column in dataframe.columns]
            missing_columns = validate_sheet_columns(sheet_name, columns)

            if missing_columns:
                # A canonical sheet name does not guarantee canonical source
                # columns. Re-run the generic detector so aliases such as
                # "Enrollment Number" and "Mail ID" are handled consistently.
                detected_definition, detected_dataframe, detected_metadata = (
                    _detected_sheet_definition(sheet_name, dataframe)
                )

                if (
                    detected_definition is not None
                    and detected_definition.name == definition.name
                    and not detected_metadata.get("missing_columns")
                ):
                    dataframe = detected_dataframe
                    detection_metadata = detected_metadata
                else:
                    errors.append(
                        {
                            "sheet": sheet_name,
                            "error": "MISSING_REQUIRED_COLUMNS",
                            "missing_columns": missing_columns,
                        }
                    )
                    continue
            else:
                canonical_df = dataframe.copy()
                canonical_df.columns = columns
                canonical_df = canonical_df.rename(
                    columns=_resolve_column_aliases(definition, columns)
                )
                dataframe = canonical_df

        # Multiple source sheets may represent the same entity. Merge them
        # before planning so duplicate detection/entity resolution can handle
        # the combined dataset instead of silently dropping one sheet.
        if definition.name in mapped_sheets:
            existing = mapped_sheets[definition.name]["data"]
            merged = pd.concat(
                [existing, dataframe],
                ignore_index=True,
                sort=False,
            ).fillna("")
            mapped_sheets[definition.name]["data"] = merged
            mapped_sheets[definition.name]["columns"] = list(merged.columns)
            mapped_sheets[definition.name]["row_count"] = len(merged)
            mapped_sheets[definition.name].setdefault("source_sheets", []).append(sheet_name)
            continue

        mapped_sheets[definition.name] = {
            "data": dataframe,
            "columns": list(dataframe.columns),
            "row_count": len(dataframe),
            "source_sheets": [sheet_name],
        }

        if detection_metadata is not None:
            mapped_sheets[definition.name]["detection"] = detection_metadata

    if not mapped_sheets:
        errors.append(
            {
                "sheet": None,
                "error": "NO_SUPPORTED_SHEETS",
                "message": (
                    "Workbook does not contain any supported COE Management "
                    "System sheets or detectable supported entities"
                ),
            }
        )

    return {
        "sheets": mapped_sheets,
        "errors": errors,
        "valid": not errors,
    }

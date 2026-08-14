"""
ImportDefinition — declarative, per-entity configuration for the reusable
Excel import pipeline. The pipeline (import_service.py) stays generic;
all entity-specific knowledge lives here.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class FieldMapping:
    canonical_name: str
    accepted_variants: list[str]
    required: bool = True


@dataclass
class ImportDefinition:
    import_type: str
    field_mappings: list[FieldMapping]
    identity_field: str  # the field used to detect duplicate/existing records
    resolve_references: Callable  # (db, record) -> (record_with_resolved_ids, category, errors)
    persist_record: Callable  # (record) -> ORM model instance ready for db.add()
    normalize_record: Callable  # (record) -> normalized record


def normalize_default(record: dict) -> dict:
    normalized = {}
    for k, v in record.items():
        if k.startswith("_"):
            normalized[k] = v
            continue
        value = "" if v is None else str(v).strip()
        normalized[k] = value
    return normalized


IMPORT_DEFINITIONS: dict[str, ImportDefinition] = {}


def register_definition(definition: ImportDefinition):
    IMPORT_DEFINITIONS[definition.import_type] = definition


def get_definition(import_type: str) -> ImportDefinition:
    if import_type not in IMPORT_DEFINITIONS:
        raise ValueError(f"Unknown import_type: {import_type}")
    return IMPORT_DEFINITIONS[import_type]
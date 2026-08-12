import json
from pathlib import Path

MAPPING_PATH = Path(__file__).parent / "mappings" / "students.json"

def load_mapping_rules() -> dict:
    with open(MAPPING_PATH, "r") as f:
        return json.load(f)

def map_columns(excel_columns: list) -> dict:
    rules = load_mapping_rules()
    mapping = {}

    for col in excel_columns:
        normalized_col = col.strip().lower()
        for canonical_field, variants in rules.items():
            if normalized_col in [v.lower() for v in variants]:
                mapping[col] = canonical_field
                break

    return mapping
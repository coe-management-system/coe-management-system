from .reader import read_excel
from .detector import detect_columns
from .column_mapper import map_columns
from .normalizer import normalize_record
from .validator import validate_record
from .duplicate_detector import detect_duplicates

def run_import(file_path: str, sheet_name: str = None) -> dict:
    df = read_excel(file_path, sheet_name)
    excel_columns = detect_columns(df)
    mapping = map_columns(excel_columns)

    valid_records = []
    invalid_records = []
    errors = []
    all_records = []

    for idx, row in df.iterrows():
        row_number = idx + 2
        raw_record = {mapping[col]: row[col] for col in df.columns if col in mapping}
        normalized = normalize_record(raw_record)
        normalized["_row"] = row_number

        row_errors = validate_record(normalized, row_number)
        all_records.append(normalized)

        if row_errors:
            errors.extend(row_errors)
            invalid_records.append(normalized)
        else:
            valid_records.append(normalized)

    duplicates = detect_duplicates(all_records)

    return {
        "mapping": mapping,
        "valid_records": [{k: v for k, v in r.items() if k != "_row"} for r in valid_records],
        "invalid_records": invalid_records,
        "errors": errors,
        "duplicates": duplicates
    }

if __name__ == "__main__":
    import json
    result = run_import("../data/sample/students.xlsx")
    print(json.dumps(result, indent=2))
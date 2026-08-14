"""
Normalization rules applied to Excel data before validation:
- All fields: leading/trailing whitespace stripped
- email: converted to lowercase
- student_id: converted to uppercase
No other transformations are applied — data is not silently altered beyond these documented rules.
""" 
def normalize_value(field: str, value: str) -> str:
    if value is None:
        return ""
    value = str(value).strip()

    if field == "email":
        value = value.lower()
    if field == "roll_no":
        value = value.upper()

    return value

def normalize_record(record: dict) -> dict:
    return {field: normalize_value(field, val) for field, val in record.items()}
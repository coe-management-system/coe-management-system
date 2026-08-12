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
import re

REQUIRED_FIELDS = ["roll_no", "name", "email", "department", "batch", "group"]
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_record(record: dict, row_number: int) -> list:
    errors = []

    for field in REQUIRED_FIELDS:
        if not record.get(field, "").strip():
            errors.append({"row": row_number, "field": field, "error": f"Missing required field: {field}"})

    email = record.get("email", "")
    if email and not EMAIL_REGEX.match(email):
        errors.append({"row": row_number, "field": "email", "error": "Invalid email format"})

    return errors
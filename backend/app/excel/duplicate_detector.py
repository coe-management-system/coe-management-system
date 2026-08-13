def detect_duplicates(records: list) -> list:
    seen = {}
    duplicates = []

    for record in records:
        student_id = record.get("student_id", "")
        if not student_id:
            continue
        if student_id in seen:
            duplicates.append({
                "student_id": student_id,
                "rows": [seen[student_id], record["_row"]]
            })
        else:
            seen[student_id] = record["_row"]

    return duplicates
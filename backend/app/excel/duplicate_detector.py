def detect_duplicates(records: list) -> list:
    seen = {}
    duplicates = []

    for record in records:
        roll_no = record.get("roll_no", "")
        if not roll_no:
            continue
        if roll_no in seen:
            duplicates.append({
                "roll_no": roll_no,
                "rows": [seen[roll_no], record["_row"]]
            })
        else:
            seen[roll_no] = record["_row"]

    return duplicates
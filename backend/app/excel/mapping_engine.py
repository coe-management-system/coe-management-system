"""
Generic column-mapping engine shared by all import types.
Given a list of FieldMapping configs and the actual Excel column headers,
produces a mapping result classifying each column as MAPPED, UNKNOWN,
or AMBIGUOUS.
"""


def map_columns_for_definition(excel_columns: list[str], field_mappings) -> dict:
    """
    Returns:
    {
        "mapping": {excel_col: canonical_field},
        "unmapped_columns": [...],
        "ambiguous_columns": [{"column": ..., "possible_mappings": [...], "reason": ...}],
        "column_status": [{"excel_column": ..., "system_field": ..., "status": "MAPPED"|"IGNORED"|"AMBIGUOUS"}]
    }
    """
    mapping = {}
    unmapped = []
    ambiguous = []
    column_status = []

    for col in excel_columns:
        normalized_col = col.strip().lower()
        matches = []
        for fm in field_mappings:
            if normalized_col in [v.lower() for v in fm.accepted_variants]:
                matches.append(fm.canonical_name)

        if len(matches) == 1:
            mapping[col] = matches[0]
            column_status.append({"excel_column": col, "system_field": matches[0], "status": "MAPPED"})
        elif len(matches) > 1:
            ambiguous.append({
                "column": col,
                "possible_mappings": matches,
                "reason": f"Column '{col}' matches multiple canonical fields: {matches}",
            })
            column_status.append({"excel_column": col, "system_field": None, "status": "AMBIGUOUS"})
        else:
            unmapped.append(col)
            column_status.append({"excel_column": col, "system_field": None, "status": "IGNORED"})

    return {
        "mapping": mapping,
        "unmapped_columns": unmapped,
        "ambiguous_columns": ambiguous,
        "column_status": column_status,
    }
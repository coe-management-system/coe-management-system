from app.excel.import_definitions import FieldMapping
from app.excel.mapping_engine import map_columns_for_definition


def test_ambiguous_column_detected():
    field_mappings = [
        FieldMapping("name", ["Name", "Student Name"]),
        FieldMapping("department", ["Department", "Dept", "Name"]),  # deliberate overlap
    ]
    result = map_columns_for_definition(["Name"], field_mappings)
    assert result["mapping"] == {}
    assert len(result["ambiguous_columns"]) == 1
    assert set(result["ambiguous_columns"][0]["possible_mappings"]) == {"name", "department"}
    assert result["column_status"][0]["status"] == "AMBIGUOUS"


def test_unmapped_column_ignored():
    field_mappings = [FieldMapping("name", ["Name"])]
    result = map_columns_for_definition(["Notes"], field_mappings)
    assert result["unmapped_columns"] == ["Notes"]
    assert result["mapping"] == {}
    assert result["column_status"][0]["status"] == "IGNORED"


def test_clean_mapping_no_ambiguity():
    field_mappings = [FieldMapping("email", ["Email", "E-mail"])]
    result = map_columns_for_definition(["E-mail"], field_mappings)
    assert result["mapping"] == {"E-mail": "email"}
    assert result["ambiguous_columns"] == []
    assert result["column_status"][0]["status"] == "MAPPED"


def test_department_field_mappings_no_ambiguity_in_practice():
    """
    Regression guard: Department's real field mappings (code/name) must never
    collide with each other under normal Excel headers.
    """
    dept_field_mappings = [
        FieldMapping("code", ["code", "dept code", "department code", "dept_code"]),
        FieldMapping("name", ["name", "department name", "department_name", "dept name"]),
    ]
    result = map_columns_for_definition(["Code", "Name"], dept_field_mappings)
    assert result["mapping"] == {"Code": "code", "Name": "name"}
    assert result["ambiguous_columns"] == []
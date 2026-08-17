from pathlib import Path

import pandas as pd


SUPPORTED_SHEETS = {
    "Departments",
    "Batches",
    "Groups",
    "Students",
    "Subjects",
    "Companies",
    "Technologies",
    "Training",
    "Attendance",
}


class WorkbookReadError(Exception):
    """Raised when the workbook cannot be read safely."""


def get_workbook_sheet_names(file_path: str) -> list[str]:
    """
    Return all worksheet names from an Excel workbook.
    """
    path = Path(file_path)

    if not path.exists():
        raise WorkbookReadError(f"Excel file not found: {file_path}")

    try:
        excel_file = pd.ExcelFile(path)
        return excel_file.sheet_names
    except Exception as exc:
        raise WorkbookReadError(
            "Unable to read Excel workbook"
        ) from exc


def read_workbook(file_path: str) -> dict[str, pd.DataFrame]:
    """
    Read all worksheets from the workbook.

    Returns:
        {
            "Departments": DataFrame,
            "Batches": DataFrame,
            ...
        }

    Unknown sheets are preserved instead of silently discarded.
    """
    path = Path(file_path)

    if not path.exists():
        raise WorkbookReadError(f"Excel file not found: {file_path}")

    try:
        excel_file = pd.ExcelFile(path)
    except Exception as exc:
        raise WorkbookReadError(
            "Unable to read Excel workbook"
        ) from exc

    workbook = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            dtype=str,
        )

        df = df.fillna("")

        # Normalize only the column-header whitespace.
        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        workbook[sheet_name] = df

    return workbook


def get_supported_sheets(
    workbook: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """
    Return only sheets recognized by the master workbook importer.
    """
    return {
        sheet_name: dataframe
        for sheet_name, dataframe in workbook.items()
        if sheet_name.strip().lower()
        in {name.lower() for name in SUPPORTED_SHEETS}
    }


def get_unknown_sheets(
    workbook: dict[str, pd.DataFrame],
) -> list[str]:
    """
    Return workbook sheets that are not currently supported.
    """
    supported = {
        name.lower()
        for name in SUPPORTED_SHEETS
    }

    return [
        sheet_name
        for sheet_name in workbook
        if sheet_name.strip().lower() not in supported
    ]
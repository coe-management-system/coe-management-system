import pandas as pd
from pathlib import Path


def get_sheet_names(file_path: str) -> list:
    with pd.ExcelFile(file_path) as xls:
        return xls.sheet_names


def read_excel(file_path: str, sheet_name: str = None) -> pd.DataFrame:
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    if Path(file_path).suffix.lower() == ".csv":
        df = pd.read_csv(file_path, dtype=str)
        df = df.fillna("")
        return df

    if sheet_name is None:
        sheets = get_sheet_names(file_path)
        sheet_name = sheets[0]

    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
    df = df.fillna("")
    return df


def read_sheet(
    file_path: str,
    sheet_name: str = None,
    header_row: int = 0,
) -> tuple[pd.DataFrame, list]:
    """
    Reads a sheet into a raw, type-preserving DataFrame (dtype=object).

    Unlike `read_excel`, cells keep their original Python types (datetime,
    float, int, str, None) so callers can inspect each cell individually
    instead of assuming a column-wide dtype. Empty cells become None.

    Returns (df, sheet_names).
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    suffix = Path(file_path).suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path, header=header_row, dtype=object)
        return df, []

    if sheet_name is None:
        sheet_names = get_sheet_names(file_path)
        sheet_name = sheet_names[0]
    else:
        sheet_names = [sheet_name]

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=header_row,
        dtype=object,
    )
    return df, sheet_names

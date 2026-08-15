import pandas as pd
from pathlib import Path

def get_sheet_names(file_path: str) -> list:
    with pd.ExcelFile(file_path) as xls:
        return xls.sheet_names

def read_excel(file_path: str, sheet_name: str = None) -> pd.DataFrame:
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    if sheet_name is None:
        sheets = get_sheet_names(file_path)
        sheet_name = sheets[0]

    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
    df = df.fillna("")
    return df
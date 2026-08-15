"""
Manual performance baseline script -- not part of pytest suite.
Run directly: python tests/perf/measure_import_baseline.py
"""
import time
import openpyxl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.services.import_service import ImportService

ROW_COUNTS = [100, 1000, 5000]
OUT_DIR = Path(__file__).parent


def generate_file(n_rows: int) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Roll No", "Name", "Email", "Department", "Batch", "Group"])
    for i in range(n_rows):
        ws.append([f"21CS{i:04d}", f"Student {i}", f"student{i}@test.com", "CSE", "2026", "4A"])
    path = OUT_DIR / f"baseline_{n_rows}.xlsx"
    wb.save(path)
    return path


def measure(n_rows: int):
    file_path = generate_file(n_rows)
    file_size_kb = file_path.stat().st_size / 1024

    db = SessionLocal()
    try:
        job = ImportService.create_import(db, str(file_path), file_path.name, created_by=2)

        t0 = time.perf_counter()
        ImportService.validate_import(db, job)
        t1 = time.perf_counter()

        commit_result = ImportService.commit_import(db, job)
        t2 = time.perf_counter()

        print(f"rows={n_rows:>5}  file_kb={file_size_kb:>8.1f}  "
              f"validate_s={t1 - t0:>7.3f}  commit_s={t2 - t1:>7.3f}  total_s={t2 - t0:>7.3f}  "
              f"imported={commit_result['imported_count']}")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"{'rows':>10}{'file_kb':>12}{'validate_s':>14}{'commit_s':>12}{'total_s':>12}{'imported':>12}")
    for n in ROW_COUNTS:
        measure(n)

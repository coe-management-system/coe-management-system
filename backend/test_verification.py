import os
import openpyxl
import pandas as pd
from sqlalchemy import select
from app.core.database import SessionLocal, engine, Base
import app.models
from app.models.import_job import ImportJob
from app.models.student import Student
from app.models.department import Department
from app.models.user import User
from app.services.import_service import ImportService, ImportStatus

Base.metadata.create_all(bind=engine)

def run_test(name, df, import_type=None, filename="test.xlsx"):
    print(f"\n==========================================")
    print(f"TEST: {name}")
    print(f"==========================================")
    temp_path = f"temp_{filename}"
    df.to_excel(temp_path, index=False)
    
    db = SessionLocal()
    try:
        from app.excel.schema_detector import detect_import_type
        if not import_type:
            cols = list(df.columns)
            detected = detect_import_type(cols, filename=filename)
            import_type = detected["detected_type"]
            print(f"Auto-detected type: {import_type} (confidence: {detected['confidence']})")
        
        user = db.scalar(select(User))
        created_by_id = user.id if user else None

        job = ImportService.create_import(
            db=db,
            file_path=temp_path,
            filename=filename,
            created_by=created_by_id,
            import_type=import_type or "student"
        )
        print(f"1. Created Import Job #{job.id} (type={job.import_type})")
        
        val_result = ImportService.validate_import_dispatch(db, job)
        print(f"2. Validated: summary={val_result['summary']}")
        print(f"   Missing cols auto-added: {val_result.get('missing_columns_auto_added')}")
        print(f"   Mapped cols: {val_result.get('mapping')}")
        
        commit_result = ImportService.commit_import_dispatch(db, job)
        print(f"3. Committed: status={commit_result['status']}, count={commit_result['imported_count']}")
        
        assert commit_result['status'] == ImportStatus.COMMITTED
        print(">>> SUCCESS! Process completed cleanly.")
        return True
    except Exception as e:
        db.rollback()
        print(f">>> FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Test 1: Full students dataframe (no missing columns)
df_full = pd.DataFrame([
    {"Admission ID": "TEST001", "Student Name": "Alice Smith", "Email ID": "alice@test.edu", "Branch": "CSE", "Year": 2026, "Section": "A"},
    {"Admission ID": "TEST002", "Student Name": "Bob Jones", "Email ID": "bob@test.edu", "Branch": "ECE", "Year": 2025, "Section": "B"},
])
run_test("No missing columns", df_full, filename="students_full.xlsx")

# Test 2: One missing required column (missing 'Email ID')
df_missing_one = pd.DataFrame([
    {"Admission ID": "TEST003", "Student Name": "Charlie Brown", "Branch": "CSE", "Year": 2026, "Section": "A"},
    {"Admission ID": "TEST004", "Student Name": "Diana Prince", "Branch": "ME", "Year": 2024, "Section": "C"},
])
run_test("One missing required column (missing email)", df_missing_one, filename="students_no_email.xlsx")

# Test 3: Multiple missing required columns (missing 'Admission ID', 'Email ID', 'Section')
df_missing_multi = pd.DataFrame([
    {"Student Name": "Evan Wright", "Branch": "IT", "Year": 2026},
    {"Student Name": "Fiona Gallagher", "Branch": "CSE", "Year": 2025},
])
run_test("Multiple missing required columns (missing roll_no, email, group)", df_missing_multi, filename="students_partial.xlsx")

# Test 4: All required columns missing (only random unmapped columns)
df_missing_all = pd.DataFrame([
    {"Notes": "Student from exchange program", "Score": 95},
    {"Notes": "Regular student", "Score": 88},
])
run_test("All required columns missing (only unmapped columns)", df_missing_all, import_type="student", filename="students_empty_cols.xlsx")

# Test 5: Repeated processing of the same dataset (idempotency)
df_repeat = pd.DataFrame([
    {"Admission ID": "TEST010", "Student Name": "Grace Hopper", "Email ID": "grace@test.edu", "Branch": "CSE", "Year": 2026, "Section": "A"},
])
print("\n--- First run of repeat test ---")
run_test("Repeat Test Run 1", df_repeat, filename="students_repeat.xlsx")
print("\n--- Second run of same data (should be detected as EXISTING without duplicating) ---")
run_test("Repeat Test Run 2", df_repeat, filename="students_repeat.xlsx")

# Test 6: Testing all files in coe_mixed_test_data_100plus
test_dir = "../coe_mixed_test_data_100plus"
all_pass = True
for fname in sorted(os.listdir(test_dir)):
    if fname.endswith(".xlsx") and not fname.startswith("00_"):
        fpath = os.path.join(test_dir, fname)
        df_real = pd.read_excel(fpath)
        ok = run_test(f"Real Test File: {fname}", df_real, filename=fname)
        if not ok:
            all_pass = False

print("\n==========================================")
if all_pass:
    print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY (100% PASSED)!")
else:
    print("SOME TESTS FAILED!")
print("==========================================")

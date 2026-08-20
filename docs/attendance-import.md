# Attendance Calculator — Excel Import Hardening

This document explains how the attendance calculator import works after the
hardening changes, the supported upload shapes, and the behaviour changes versus
the previous implementation.

## Supported upload formats

Two real-world layouts are supported and detected **from the column headers,
never from the filename**:

**Format A — wide grid** (one row per student, one column per date):

```
Serial No. | Roll No. | Admission ID | Student Name | Branch | Section | 01-Aug-2026 | 02-Aug-2026 | ...
```

**Format B — transaction log** (one row per attendance event):

```
Addmission No | Roll No | Subject | Date | Attendance Status
```

Rows / headers in either format may use common variants (Roll No/Roll Number,
Addmission No/Admission ID, Subject/Subject Code, etc.). Detection is handled by
`detect_attendance_format` in `backend/app/excel/attendance_parser.py`.

## How a mark is interpreted

- Marks are case-insensitive: `P / p / Present` → `PRESENT`, `A / Absent` → `ABSENT`,
  `L / OD / Leave` → `LEAVE`, `H / Holiday / Cancelled / Off` → `HOLIDAY`.
- **Blank cells are "not marked"** — they are excluded from the *Total Classes Held*
  denominator and are *not* counted as absent. They are flagged in the preview.
- Unrecognised values (`x`, `?`, `banana`, …) are flagged as invalid marks and
  excluded from calculations — never silently coerced.

## Attendance percentage

`Attendance % = (Present ÷ Total Classes Held) × 100`

- `Total Classes Held` = rows with status `PRESENT` or `ABSENT`.
- `HOLIDAY` and `LEAVE` are excluded from the denominator by default.
  Set `ATTENDANCE_LEAVE_COUNTS_AS_HELD=True` to count `LEAVE` as a held class.
- The denominator therefore *excludes* blank (not-marked) cells. This matches the
  ERP calculation where a day without a mark is not treated as a class day for
  that student.

## Subject resolution

For a wide grid there is no subject column in the spec, so the subject is resolved
in this order:

1. **Explicit** — the `subject` form field on the upload page.
2. **Subject column** — if the sheet has a Subject/Subject Code column, the first
   non-empty value is used.
3. **Filename hint** — a subject-like token in the filename (e.g.
   `attendance_math101_g1.xlsx` → `MATH101`).

If none apply, every row is flagged with a `subject_required` issue and nothing is
committed (the import fails safe — it never invents a subject).

For a transaction log, each row's `Subject` column is used directly.

## No silent auto-provisioning

- A student reference that does not exist in the student master is flagged
  (`REFERENCE_ERROR`) — **no placeholder student is created**.
- A subject code that does not exist in the subjects master is flagged the same way.
- Out-of-range numeric references (e.g. `999999`, `9999`) are treated as
  sentinels and flagged, never recorded. Thresholds:
  `ATTENDANCE_SENTINEL_ROLL_THRESHOLD` (default `100000`) and
  `ATTENDANCE_SENTINEL_SUBJECT_THRESHOLD` (default `9000`).

## Bad dates are never coerced

Every date cell is parsed individually. Unparseable values (e.g. `not-a-date`)
are flagged and the row is excluded. Dates are **never** silently replaced with
today's date or `NaT` (this was a source of wrong percentages in the old code).

## Idempotency & re-uploads

- Each attendance row is upserted by `(student, subject, session_date)`.
- Re-uploading the same file does **not** double-count: matching rows are
  detected as `EXISTING` and left untouched; the aggregate totals are always
  recomputed from the per-event table, so the result is the same after every run.
- If the same event is uploaded with a *different* mark, the existing row is
  **overwritten** and the change is recorded in the `overwritten` audit list.

## Student aggregates

The student master gains these computed columns (see the migration
`5f6a1b2c3d4e_attendance_hardening`):

- `total_classes_held`, `total_present`, `total_absent`, `attendance_percentage`
- `attendance_updated_at`, `attendance_source_file`
- `admission_id` (unique) — used as a second student identity key

## Configuration (`.env` / `backend/app/core/config.py`)

| Setting | Default | Meaning |
| --- | --- | --- |
| `ATTENDANCE_THRESHOLD_PERCENT` | `75.0` | Below this % a student is flagged in exports |
| `ATTENDANCE_LEAVE_COUNTS_AS_HELD` | `False` | Count `LEAVE` in *Total Classes Held* |
| `ATTENDANCE_UPDATE_MODE` | `cumulative` | Future-proofing for overwrite vs additive |
| `ATTENDANCE_SENTINEL_ROLL_THRESHOLD` | `100000` | Numeric roll values ≥ this are sentinels |
| `ATTENDANCE_SENTINEL_SUBJECT_THRESHOLD` | `9000` | Numeric subject codes ≥ this are sentinels |

## API

All endpoints are under `/api/v1/imports`:

| Endpoint | Purpose |
| --- | --- |
| `POST /{id}/validate` | Parse + resolve + classify, returns preview payload |
| `POST /{id}/commit` | Upsert events, recompute aggregates, return write report |
| `GET /{id}/attendance/flagged` | Detailed flagged-rows report |
| `GET /{id}/attendance/export` | Download updated attendance `.xlsx` (below-threshold rows highlighted red) |

The validate endpoint now also accepts `subject` (form field) and `.csv` files.

## Behaviour changes (vs the old implementation)

1. Roll-number columns (e.g. `Roll No.`) are mapped correctly; student identity
   is resolved by roll **or** admission ID.
2. Wide-grid date columns are parsed and used; no more auto-filling missing
   subject/date/status with today's date / "present".
3. Marks are normalised (`p`/`P`/`Present` all count as `PRESENT`) so the
   percentage calculator no longer sees `0.0%` for valid marks.
4. Unmatched students/subjects and sentinels are **flagged, not auto-created**.
5. Blank cells exclude the day from classes held instead of becoming a bogus
   present/absent row.
6. Re-imports are idempotent; overwrites are logged.
7. The updated sheet can be downloaded after commit, with below-threshold
   students highlighted red.

## Tests

- `backend/tests/unit/test_attendance_parser.py` — parser unit tests.
- `backend/tests/unit/test_attendance_import_service.py` — end-to-end service
  tests (percentages, idempotency, overwrites, export) on in-memory SQLite.

## Migration

Run `alembic upgrade head` against the real database to apply
`5f6a1b2c3d4e_attendance_hardening` (adds the student aggregate/admission columns,
attendance audit columns, and `import_jobs.subject_hint`).
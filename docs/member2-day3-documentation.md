\# Day 3 — Student Import Workflow



\*\*Module:\*\* Bulk Student Import (Excel)

\*\*Owner:\*\* Member 2

\*\*Status:\*\* Complete — 110/110 tests passing

\*\*Branch:\*\* `feature/member2-day3-import-workflow`



\---



\## 1. Overview



The import workflow lets faculty upload an Excel file (`.xlsx` / `.xls`) of

student records, preview a deterministic validation report with zero writes,

then commit only the valid rows inside a single transaction. Nothing is

written to the `students` table until commit, and commit either fully

succeeds or fully rolls back.



The workflow is a three-step state machine, one HTTP call per step:
POST /imports → registers the upload, computes file hash

POST /imports/{id}/validate → runs the full pipeline, produces a preview (no writes)

POST /imports/{id}/commit → inserts only VALID rows, inside a transaction
---



\## 2. Supported formats \& upload constraints



| Constraint | Rule |

|---|---|

| Extensions | `.xlsx`, `.xls` only |

| Content types | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/vnd.ms-excel`, `application/octet-stream` |

| Max file size | 10 MB |

| Empty file | Rejected (0 bytes) |

| Empty workbook | Rejected (no worksheets, or no header/data rows in first 2 rows of the first sheet) |

| Corrupt workbook | Rejected — file must load with `openpyxl` |

| Auth | All endpoints require an authenticated user with the `faculty` role |



All of the above is enforced in `create\_import` (route layer) \*\*before\*\* the

file is handed to `ImportService`, so a bad upload never reaches the

database.



\---



\## 3. Status lifecycle
CREATED ──validate──▶ PROCESSING ──▶ PREVIEW\_READY ──commit──▶ COMMITTED

│ │ │

└───────────────────────┴────────────(exception)───────────▶ FAILED
| Status | Meaning |

|---|---|

| `created` | Upload accepted, file hashed and stored, no rows processed yet |

| `processing` | Validation pipeline is running (transient) |

| `preview\_ready` | Validation complete; preview stored on the job; ready to commit |

| `committed` | Valid rows inserted as students; terminal, successful state |

| `failed` | An exception occurred during validate or commit; terminal, error state |

| `rejected` | Reserved for future manual-rejection flow (not currently set by any endpoint) |



Rules enforced by the service layer:

\- `validate\_import` only accepts jobs in `created` or `failed` (so a failed

&#x20; validation can be retried on the same job).

\- `commit\_import` only accepts jobs in `preview\_ready`, and requires a

&#x20; stored `validation\_result` — it never re-reads the Excel file.



\---



\## 4. Per-row categorization (validation)



Every row in the sheet is resolved to exactly one category during

`validate\_import`:



| Category | Meaning |

|---|---|

| `VALID` | Passed field validation, department/batch/group all resolved, roll number not already a student, not a duplicate within the file |

| `INVALID` | Failed field-level validation (e.g. malformed email) |

| `REFERENCE\_ERROR` | Field-level validation passed but department, batch, or group could not be resolved to an existing entity |

| `EXISTING` | Roll number already belongs to a student in the database |

| `DUPLICATE` | Same roll number appears more than once within the uploaded file (first occurrence keeps its earlier category; later occurrences are marked `DUPLICATE`) |



Reference errors carry a structured `error\_code` (`UNKNOWN\_DEPARTMENT`,

`UNKNOWN\_BATCH`, `UNKNOWN\_GROUP`) plus the offending field and value, so the

frontend can render specific messages without parsing free text.



\*\*Only rows categorized `VALID` are inserted on commit.\*\* Everything else is

surfaced in the preview for the user to fix and re-upload.



\---



\## 5. Repeated-upload / file-hash behavior



Every upload is hashed with SHA-256 (`compute\_file\_hash`). If a file with an

identical hash was already uploaded (any filename), `create\_import` still

creates a new `ImportJob`, but flags it internally

(`\_is\_repeat\_upload` / `\_original\_import\_id`) so the caller can detect and

warn about re-uploading the same content — the system does not block the

re-upload outright.



\---



\## 6. Rollback behavior



`commit\_import` wraps all student inserts in a single transaction:



\- Rows are added to the session one at a time (`db.add`), but nothing is

&#x20; flushed to the database until `db.commit()` is called once, after every

&#x20; valid row has been queued.

\- If \*\*any\*\* exception occurs during that loop, `db.rollback()` is called,

&#x20; the job is marked `failed` with the exception message stored in

&#x20; `error\_message`, and the exception is re-raised. No partial set of

&#x20; students is ever left in the database.

\- On successful commit, the temporary uploaded file on disk is deleted.



\---



\## 7. Integration contract for Member 1



Base path: `/imports`. All endpoints require a valid auth token for a user

with the `faculty` role (`403` otherwise, `401` if unauthenticated).



\### `POST /imports`

Registers an upload. Multipart form field: `file`.



\*\*201 response\*\* (`ImportCreateResponse`):

```json

{

&#x20; "import\_id": 12,

&#x20; "filename": "students.xlsx",

&#x20; "status": "created",

&#x20; "file\_hash": "a1b2c3..."

}

```

\*\*400\*\* — bad extension, bad content type, empty file, unreadable/corrupt workbook, file too large.



\### `GET /imports`

Lists recent import jobs, newest first (default limit 50).



\*\*200 response\*\* — array of `ImportDetailResponse` (see below).



\### `GET /imports/{import\_id}`

Fetches a single job's current state/counters.



\*\*200 response\*\* (`ImportDetailResponse`):

```json

{

&#x20; "import\_id": 12,

&#x20; "filename": "students.xlsx",

&#x20; "status": "preview\_ready",

&#x20; "created\_by": 3,

&#x20; "created\_at": "2026-08-12T09:15:00Z",

&#x20; "completed\_at": null,

&#x20; "total\_rows": 40,

&#x20; "valid\_rows": 35,

&#x20; "invalid\_rows": 3,

&#x20; "duplicate\_rows": 2,

&#x20; "error\_message": null

}

```

\*\*404\*\* — import not found.



\### `POST /imports/{import\_id}/validate`

Runs the pipeline; writes nothing to `students`.



\*\*200 response\*\* (`ValidateImportResponse`):

```json

{

&#x20; "import\_id": 12,

&#x20; "status": "preview\_ready",

&#x20; "mapping": { "Roll No": "roll\_no", "Name": "name", "...": "..." },

&#x20; "unmapped\_columns": \["Notes"],

&#x20; "summary": {

&#x20;   "total\_rows": 40,

&#x20;   "valid": 35,

&#x20;   "invalid": 1,

&#x20;   "reference\_errors": 2,

&#x20;   "existing": 0,

&#x20;   "duplicates": 2,

&#x20;   "ready\_to\_commit": 35

&#x20; },

&#x20; "records": \[

&#x20;   {

&#x20;     "roll\_no": "21CS045",

&#x20;     "name": "...",

&#x20;     "email": "...",

&#x20;     "row": 5,

&#x20;     "category": "REFERENCE\_ERROR",

&#x20;     "field\_errors": \[],

&#x20;     "reference\_errors": \[

&#x20;       {

&#x20;         "field": "department",

&#x20;         "value": "CSEE",

&#x20;         "error\_code": "UNKNOWN\_DEPARTMENT",

&#x20;         "message": "Department 'CSEE' not found"

&#x20;       }

&#x20;     ],

&#x20;     "resolved\_department\_id": null,

&#x20;     "resolved\_batch\_id": null,

&#x20;     "resolved\_group\_id": null,

&#x20;     "existing\_student\_id": null

&#x20;   }

&#x20; ]

}

```

\*\*404\*\* — import not found. \*\*409\*\* — wrong status for validation (must be `created` or `failed`).



\### `POST /imports/{import\_id}/commit`

Inserts only `VALID` rows, transactionally.



\*\*200 response\*\* (`CommitImportResponse`):

```json

{

&#x20; "import\_id": 12,

&#x20; "status": "committed",

&#x20; "imported\_count": 35,

&#x20; "imported\_students": \["21CS001", "21CS002", "..."]

}

```

\*\*404\*\* — import not found. \*\*409\*\* — wrong status (must be `preview\_ready`, or no stored validation result).



\---



\## 8. Error response shape



All error responses use FastAPI's standard shape:

```json

{ "detail": "human-readable message" }

```

`400` — request/upload-level problems. `404` — unknown import id. `409` —

invalid state transition. `500` — unexpected internal failure (validation

or commit exception not otherwise categorized); the job is marked `failed`

with the exception message stored server-side in `error\_message`.


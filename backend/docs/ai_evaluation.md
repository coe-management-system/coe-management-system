# AI Evaluation Dataset & Baseline

This document tracks the Day 2 performance of the AI tool selection, tool success, and AI grounding mechanisms. It serves as a baseline before implementing more advanced features like RAG, Voice, or Multi-agent workflows.

## Evaluation Questions

| Question | Expected Tool | Selected Tool | Correct Tool? | Tool Success? | Grounded? | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| "Tell me about student CSE101." | `get_student` | `get_student` | Yes | Yes | Yes | 0.5s |
| "What is the roll number of Rahul?" | `get_students` | `get_students` | Yes | Yes | Yes | 0.8s |
| "Which students have attendance below 75%?" | `get_low_attendance_students` | `get_low_attendance_students` | Yes | Yes | Yes | 0.4s |
| "Who is missing classes?" | `get_low_attendance_students` | `get_low_attendance_students` | Yes | Yes | Yes | 0.4s |
| "What is faculty 12's workload?" | `get_faculty_workload` | `get_faculty_workload` | Yes | Yes | Yes | 0.6s |
| "How many hours is faculty 12 teaching?" | `get_faculty_workload` | `get_faculty_workload` | Yes | Yes | Yes | 0.5s |
| "Are there timetable conflicts?" | `get_timetable_conflicts` | `get_timetable_conflicts` | Yes | Yes | Yes | 0.5s |
| "What if we move the AI lecture to Room 301?" | `run_what_if` | `run_what_if` | Yes | Yes | Yes | 0.7s |
| "Is student CSE101 certified in Python?" | `get_certification_status` | `get_certification_status` | Yes | No (Mock Pending) | Yes | 0.3s |
| "Did CSE101 finish their internship?" | `get_training_status` | `get_training_status` | Yes | No (Mock Pending) | Yes | 0.3s |

## Grounding Testing Summary

- **Empty Results**: When a tool returns no data (e.g. empty list of students), the AI accurately responds with "No matching records found." instead of hallucinating data.
- **Failures**: When a backend service throws an error, the AI catches it and responds with a sanitized error message (e.g., "Unable to retrieve requested information. Reason: ..."), without leaking DB connection strings or raw stack traces.
- **Provenance**: Each tool response includes metadata (e.g. `{"service": "student_service", "source": "postgresql"}`), explicitly identifying where the data originated.

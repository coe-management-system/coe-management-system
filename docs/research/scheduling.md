
# Scheduling Prototype

## 1. Purpose

The scheduling prototype provides the initial scheduling engine for the
COE Management System.

The current implementation focuses on three core capabilities:

1. Timetable conflict detection
2. Basic faculty workload calculation
3. What-if scheduling simulation

The prototype also includes basic priority classification and candidate
slot evaluation for rescheduling.

The implementation is intentionally lightweight and uses timetable event
data directly. It is not intended to be a production-grade optimization
engine at this stage.

---

## 2. Timetable Event Structure

Scheduling operations use a common timetable event structure.

```text
id
subject_id
faculty_id
batch_id
room_id
date
start_time
end_time
priority
```

# Scheduling Prototype

## 1. Purpose

The scheduling prototype provides the core scheduling engine for the
COE Management System.

The implementation currently supports:

1. Timetable conflict detection
2. Scheduling constraint validation
3. Priority classification
4. Faculty workload calculation
5. Candidate slot evaluation for rescheduling
6. What-if timetable simulation
7. Scheduling service coordination

The implementation is intentionally lightweight and operates on timetable
event data without directly depending on the database layer.

It is currently a scheduling decision-support prototype and does not
automatically optimize or persist timetable changes.

---

## 2. Scheduling Architecture

The scheduling functionality is organized into independent modules:

```text
app/scheduling/
│
├── domain.py
├── constraints.py
├── priorities.py
├── conflict_detector.py
├── workload_optimizer.py
├── rescheduler.py
├── what_if_simulator.py
├── service.py
└── scheduler.py
```

### Module Responsibilities

- `domain.py` — Defines the `SchedulingEvent` domain representation and
  conversion between timetable data and scheduling data.
- `constraints.py` — Validates required scheduling fields, time ranges,
  priorities, and candidate slots.
- `priorities.py` — Handles scheduling priority classification.
- `conflict_detector.py` — Detects faculty, batch, and room conflicts
  between overlapping timetable events.
- `workload_optimizer.py` — Calculates event duration and total allocated
  workload for a faculty member.
- `rescheduler.py` — Evaluates candidate timetable slots and reports
  feasibility and rejection reasons.
- `what_if_simulator.py` — Simulates proposed event changes on a copied
  timetable without modifying the original data.
- `service.py` — Provides the application-level `SchedulingService` that
  coordinates scheduling operations.
- `scheduler.py` — Contains the scheduling engine entry-point logic.

---

## 3. Timetable Event Structure

Scheduling operations use a common timetable event structure:

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

The scheduling domain uses `SchedulingEvent` as a lightweight,
database-independent representation of this structure.

---

## 4. Conflict Detection

The conflict detector checks overlapping timetable events for shared
resources.

A conflict can occur when two events overlap and use the same:

- Faculty
- Batch
- Room

Time ranges that only touch at their boundary are considered
non-overlapping.

For example:

```text
Event A: 10:00 - 11:00
Event B: 11:00 - 12:00

Result: No conflict
```

Whereas:

```text
Event A: 10:00 - 11:00
Event B: 10:30 - 11:30

Result: Conflict
```

The conflict detector returns structured conflict information including
the conflicting event IDs and conflict type.

---

## 5. Scheduling Constraints

The scheduling constraint layer validates timetable and candidate-slot
data before scheduling operations.

Current validations include:

- Required event fields
- Valid time ranges
- Equal start and end times
- Valid candidate slots
- Valid scheduling priorities

Invalid time ranges are rejected rather than being processed as valid
schedule data.

---

## 6. Priority Classification

The scheduling prototype supports priority classification for timetable
events.

The supported priority levels are:

```text
low
normal
high
urgent
```

Priority handling is kept separate from conflict detection and
rescheduling so that the scheduling engine can use it independently.

---

## 7. Faculty Workload Calculation

The workload component calculates allocated teaching hours from timetable
events.

For each event:

```text
start_time
    +
end_time
    |
    v
event duration
```

For a selected faculty member:

```text
Faculty events
      |
      v
Calculate event durations
      |
      v
Sum durations
      |
      v
Allocated hours
```

The workload calculation currently supports:

- Event duration calculation
- Faculty-based event filtering
- Total allocated hours
- Invalid time-range validation

Events belonging to other faculty members are ignored.

The current implementation does not yet calculate:

- Daily workload
- Weekly workload
- Maximum faculty capacity
- Remaining capacity
- Overloaded status
- Workload balancing
- Automatic workload optimization
- Teaching/training/administrative workload categories

These remain future extensions.

---

## 8. Candidate Slot Evaluation and Rescheduling

The rescheduling component evaluates proposed candidate slots without
automatically changing the timetable.

For each candidate slot, the engine checks whether the requested:

- Faculty
- Batch
- Room

are available during the proposed date and time.

Each candidate is classified as either:

```text
feasible
rejected
```

Rejected candidates include human-readable reasons such as:

```text
Faculty 10 is unavailable due to event 1.
Batch 201 is unavailable due to event 1.
Room 101 is unavailable due to event 1.
Candidate slot has an invalid time range.
```

The existing `find_available_slots()` function is retained for backward
compatibility and returns only feasible slots.

The `evaluate_candidate_slots()` function provides the more informative
evaluation result containing status and rejection reasons.

The current implementation does not automatically move events or perform
optimization.

---

## 9. What-If Timetable Simulation

The what-if simulator allows proposed changes to a timetable event to be
tested without modifying the original timetable.

The simulation process is:

```text
Original timetable
        |
        v
Create deep copy
        |
        v
Find target event
        |
        v
Apply proposed changes
        |
        v
Run conflict detection
        |
        v
Return simulation result
```

The result includes:

- Event ID
- Simulated event
- Detected conflicts
- Conflict status

The original timetable data remains unchanged.

If the requested event does not exist, the simulator raises a
`ValueError`.

---

## 10. Scheduling Service

`service.py` provides the application-level `SchedulingService`.

The service coordinates the scheduling modules without exposing their
implementation details to higher application layers.

Current service operations include:

### Conflict Analysis

```text
SchedulingService.analyze_conflicts()
```

Converts domain events into the scheduling data structure and delegates
conflict detection to `conflict_detector.py`.

### Faculty Workload

```text
SchedulingService.get_faculty_workload(faculty_id)
```

Calculates the allocated workload for a selected faculty member by
delegating to `workload_optimizer.py`.

The service can operate with an empty timetable and returns an empty
conflict list and zero workload when no events are present.

---

## 11. Testing

The scheduling functionality is covered by unit tests under:

```text
backend/tests/unit/
```

Current test areas include:

```text
test_candidate_generation.py
test_conflict_detector.py
test_constraints.py
test_domain.py
test_priorities.py
test_rescheduler.py
test_service.py
test_what_if_simulator.py
test_workload_optimizer.py
```

The current unit test suite contains **40 tests**, covering:

- Conflict detection
- Constraint validation
- Domain conversion
- Priority classification
- Candidate slot evaluation
- Rescheduling availability
- Scheduling service behavior
- What-if simulation
- Faculty workload calculation

Latest test execution:

```text
Ran 40 tests in 0.004s

OK
```

This confirms that the current scheduling prototype passes its unit-test
suite.

---

## 12. Current Scope

Implemented:

- Scheduling event domain representation
- Conflict detection
- Constraint validation
- Priority classification
- Faculty workload calculation
- Candidate slot evaluation
- Rescheduling availability checks
- What-if timetable simulation
- Scheduling service coordination
- Unit test coverage for the implemented scheduling functionality

---

## 13. Not Yet Implemented

The current scheduling prototype does not yet provide:

- Automatic timetable generation
- Automatic event movement
- Optimization-based timetable generation
- Workload balancing
- Faculty capacity management
- Persistent timetable updates through the scheduling engine
- Advanced scheduling optimization algorithms

These should be treated as future work rather than as implemented
features.

---

## 14. Current Development Status

The scheduling prototype is currently implemented and unit-tested.

The scheduling layer is structured as independent modules so that future
API integration, database integration, and optimization functionality can
be added without rewriting the core scheduling logic.

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
8. Hard/soft constraint evaluation with structured violations
9. Constraint-aware candidate slot generation
10. Candidate scoring and ranking
11. Rescheduling recommendation workflow
12. Workload balancing and reporting
13. What-if scenario simulation
14. R&D benchmark for the scheduling engine
15. REST API and database integration

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
├── constraint_engine.py
├── priorities.py
├── conflict_detector.py
├── workload_optimizer.py
├── rescheduler.py
├── candidate_generator.py
├── scoring.py
├── recommendation.py
├── what_if_simulator.py
├── benchmark.py
├── models_timetable.py
├── service.py
└── scheduler.py
```

### Module Responsibilities

- `domain.py` — Defines the `SchedulingEvent` domain representation and
  conversion between timetable data and scheduling data.
- `constraints.py` — Validates required scheduling fields, time ranges,
  priorities, and candidate slots.
- `constraint_engine.py` — Evaluates hard and soft scheduling constraints
  and returns structured violation information. This is the core
  constraint-aware engine introduced in the Day 3 work.
- `priorities.py` — Handles scheduling priority classification.
- `conflict_detector.py` — Detects faculty, batch, and room conflicts
  between overlapping timetable events. Provides both the original
  `detect_conflicts()` API and the Day 3 `detect_conflicts_structured()`
  that delegates to the constraint engine.
- `workload_optimizer.py` — Calculates event duration and total allocated
  workload for a faculty member. Day 3 adds `calculate_workload_impact()`
  and `calculate_workload_report()`.
- `rescheduler.py` — Evaluates candidate timetable slots and reports
  feasibility and rejection reasons.
- `candidate_generator.py` — Generates and evaluates candidate slots
  against every scheduling constraint, classifying each as feasible or
  rejected with reasons.
- `scoring.py` — Scores and ranks feasible candidates so the best slot
  can be recommended.
- `recommendation.py` — Orchestrates the rescheduling recommendation
  workflow, returning a ranked recommendation or `NO_FEASIBLE_SLOT`.
- `what_if_simulator.py` — Simulates proposed event changes on a copied
  timetable without modifying the original data. Day 3 adds
  `simulate_scenario()` for room/faculty/batch unavailability and event
  changes.
- `benchmark.py` — Builds reproducible benchmark scenarios and measures
  scheduling-engine metrics.
- `models_timetable.py` — Bridges the SQLAlchemy `TimetableEvent` table to
  the domain `SchedulingEvent` representation.
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
group_id (optional)
```

The scheduling domain uses `SchedulingEvent` as a lightweight,
database-independent representation of this structure. The Day 3 work
adds an optional `group_id` field so that group-based constraints can be
evaluated.

---

## 4. Constraint Engine and Structured Violations

The Day 3 work introduces a constraint-aware engine in `constraint_engine.py`.

Every scheduling rule is expressed as a constraint with a severity:

- `HARD` — must never be violated (e.g. faculty, batch, group, and room
  availability; valid time ranges).
- `SOFT` — violations are penalized but do not make a slot infeasible
  (e.g. workload-over-capacity and scheduling-pressure preferences).

Constraints currently evaluated:

- Faculty availability
- Batch availability
- Group availability
- Room availability
- Valid time range
- Faculty workload capacity

Each violation is reported as a structured `ConstraintViolation`:

```text
constraint_type      e.g. "faculty", "batch", "group", "room", "time", "workload"
severity             "hard" or "soft"
event_id             the event under evaluation
conflicting_event_id the event that causes the conflict (or -1)
resource             the contended resource (e.g. faculty id)
message              human-readable explanation
```

The `ConstraintEngine.evaluate()` checks an event against an existing
timetable; `ConstraintEngine.evaluate_candidate()` checks a candidate slot
against a proposed event.

---

## 5. Conflict Detection

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

## 6. Scheduling Constraints

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

## 7. Priority Classification

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

## 8. Faculty Workload Calculation and Reporting

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

**Day 3 additions:**

- Workload impact analysis for candidate slots (`calculate_workload_impact()`)
- Comprehensive workload report with per-faculty breakdown
  (`calculate_workload_report()`), including:
  - Allocated hours
  - Capacity (if provided)
  - Remaining capacity
  - Overloaded status
  - Scheduling pressure (events per day)

Events belonging to other faculty members are ignored.

The current implementation does not yet calculate:

- Daily workload
- Weekly workload
- Teaching/training/administrative workload categories

These remain future extensions.

---

## 9. Candidate Slot Evaluation, Scoring, and Rescheduling

The rescheduling component evaluates proposed candidate slots without
automatically changing the timetable.

For each candidate slot, the engine checks whether the requested:

- Faculty
- Batch
- Room
- Group (Day 3)

are available during the proposed date and time, and whether the slot
violates workload constraints.

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
Workload constraint: Faculty 10 exceeds capacity.
```

The existing `find_available_slots()` function is retained for backward
compatibility and returns only feasible slots.

The `evaluate_candidate_slots()` function provides the more informative
evaluation result containing status and rejection reasons.

**Day 3 additions:**

- `candidate_generator.py` — generates candidate slots for a given date
  range and evaluates every slot against all constraints (hard + soft),
  producing a full list with status and reasons.
- `scoring.py` — scores feasible candidates deterministically:
  - Base score 1000
  - Penalties for soft violations, workload overload, scheduling pressure
  - Bonuses for higher priority, lower time deviation, fewer moved events
  - `rank_candidates()` returns candidates sorted by score descending.
- `recommendation.py` — orchestrates the full rescheduling workflow:
  1. Find target event
  2. Generate candidate slots
  3. Evaluate candidates against all constraints
  4. Calculate workload impact for each
  5. Score and rank feasible candidates
  6. Return top recommendation with explanation, or `NO_FEASIBLE_SLOT`
     with aggregated rejection reasons

The current implementation does not automatically move events or perform
optimization.

---

## 10. What-If Timetable Simulation and Scenario Analysis

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

**Day 3 additions — Scenario simulation (`simulate_scenario()`):**

Supports four scenario types:

| Scenario type | Description |
|--------------|-------------|
| `event_change` | Change an event's room, faculty, batch, or time |
| `room_unavailable` | Mark a room as unavailable for a time window |
| `faculty_unavailable` | Mark a faculty member as unavailable |
| `batch_unavailable` | Mark a batch as unavailable |

Room/faculty/batch unavailability scenarios inject a pseudo-event with
`event_id = -1` representing the blocked resource. Conflicts with the
blocker are filtered so only events that conflict with the unavailable
resource are returned.

The result includes:
- `scenario` type
- `affected_events` (full event details for events in conflict)
- `conflicts` (structured `ConstraintViolation` list)
- `timetable_unchanged: true` — the official timetable is never modified

---

## 11. Scheduling Service and Database Integration

`service.py` provides the application-level `SchedulingService`.

The service coordinates the scheduling modules without exposing their
implementation details to higher application layers.

Current service operations include:

### Conflict Analysis

```text
SchedulingService.analyze_conflicts()
SchedulingService.analyze_conflicts_structured()
```

Converts domain events into the scheduling data structure and delegates
conflict detection to `conflict_detector.py`. The structured version
returns `ConstraintViolation` objects.

### Faculty Workload

```text
SchedulingService.get_faculty_workload(faculty_id)
SchedulingService.get_workload_report(capacities)
```

Calculates the allocated workload for a selected faculty member by
delegating to `workload_optimizer.py`. The report version returns a
complete per-faculty breakdown with capacity, remaining capacity,
overloaded status, and scheduling pressure.

### Rescheduling Recommendation

```text
SchedulingService.recommend_reschedule(event_id, candidates, capacities)
```

Orchestrates the full rescheduling recommendation workflow by delegating
to `recommendation.py`.

### What-If Simulation

```text
SchedulingService.run_what_if(scenario)
```

Runs a scenario simulation without modifying the timetable by delegating
to `what_if_simulator.py`.

### Database Integration

```text
SchedulingService.from_db(db)
```

Constructs a `SchedulingService` instance by loading timetable events
from the database via `models_timetable.load_timetable_events(db)`.
This bridges the SQLAlchemy `TimetableEvent` table to the domain
`SchedulingEvent` representation.

The service can operate with an empty timetable and returns an empty
conflict list and zero workload when no events are present.

---

## 12. Testing

The scheduling functionality is covered by unit tests under:

```text
backend/tests/unit/
```

Current test areas include:

```text
test_candidate_generation.py        # Day 2 candidate evaluation
test_candidate_generator.py         # Day 3 constraint-aware candidates
test_conflict_detector.py
test_constraint_engine.py           # Day 3 constraint engine
test_constraints.py
test_domain.py
test_priorities.py
test_recommendation.py              # Day 3 reschedule recommendation
test_rescheduler.py
test_scoring.py                     # Day 3 candidate scoring
test_service.py
test_service_day3.py                # Day 3 extended service
test_what_if_simulator.py
test_what_if_scenarios.py           # Day 3 scenario simulation
test_workload_optimizer.py
test_benchmark.py                   # Day 3 R&D benchmark
test_database_integration.py        # Day 3 DB integration (sqlite in-memory)
```

Integration/API tests under:

```text
backend/tests/integration/
test_scheduling_api.py              # Day 3 REST API + RBAC
test_auth_api.py                    # pre-existing auth integration
```

The current unit test suite contains **120+ tests**, covering:

- Conflict detection (original + structured)
- Constraint validation (original constraints + Day 3 engine)
- Domain conversion (with `group_id`)
- Priority classification (string + int input)
- Candidate slot evaluation (Day 2 + Day 3 constraint-aware)
- Candidate scoring and ranking
- Rescheduling recommendation workflow + `NO_FEASIBLE_SLOT`
- Scheduling service behavior (original + Day 3 extensions)
- What-if simulation (original + Day 3 scenarios)
- Faculty workload calculation + impact + report
- R&D benchmark
- Database integration (in-memory sqlite)
- REST API endpoints + RBAC (401/403/200)

Latest test execution:

```text
Ran 143 tests in ~5s

OK
```

This confirms that the current scheduling prototype passes its full
test suite.

---

## 13. Current Scope

Implemented:

- Scheduling event domain representation (with optional `group_id`)
- Conflict detection (original + structured `ConstraintViolation`)
- Constraint validation (original + hard/soft engine with `ConstraintEngine`)
- Priority classification
- Faculty workload calculation, impact analysis, and reporting
- Candidate slot evaluation (Day 2 + Day 3 constraint-aware generation)
- Candidate scoring and ranking
- Rescheduling recommendation workflow (`NO_FEASIBLE_SLOT` handling)
- What-if timetable simulation (original + scenario analysis)
- Scheduling service coordination (with database integration)
- REST API endpoints (timetable, workload, scheduling conflicts,
  reschedule-recommendation, what-if)
- Role-based access control for scheduling APIs
- R&D benchmark infrastructure
- Unit, integration, and API test coverage

---

## 14. Not Yet Implemented

The current scheduling prototype does not yet provide:

- Automatic timetable generation
- Automatic event movement
- Optimization-based timetable generation
- Teaching/training/administrative workload categories
- Daily/weekly workload aggregation
- Persistent timetable updates through the scheduling engine
- Advanced scheduling optimization algorithms (genetic, CSP, etc.)

The following are partially implemented in Day 3 but remain decision-support
only (no auto-apply):

- Workload balancing (reported, not auto-optimized)
- Faculty capacity management (soft/hard constraints enforced on
  candidates, not persisted)

These should be treated as future work rather than as implemented
features.

---

## 15. Current Development Status

The scheduling prototype is currently implemented, unit-tested, and
integration-tested with a full REST API layer.

The scheduling layer is structured as independent modules so that future
API integration, database integration, and optimization functionality can
be added without rewriting the core scheduling logic.

Day 3 (current) delivered:

- Constraint engine with hard/soft violations and structured reporting
- Constraint-aware candidate generation with all resource constraints
- Deterministic candidate scoring and ranking
- Rescheduling recommendation workflow with `NO_FEASIBLE_SLOT`
- What-if scenario simulation (resource unavailability + event changes)
- Workload impact analysis and comprehensive reporting
- R&D benchmark for reproducible engine metrics
- Database integration via SQLAlchemy bridge
- REST API + RBAC for scheduling operations
- Full test coverage (unit + integration)

All 143 tests pass (unit + integration + auth).

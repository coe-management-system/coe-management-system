# Workload Optimization Prototype

## Purpose

The current workload component provides basic faculty workload
calculation from timetable events.

The implementation focuses on calculating total allocated teaching hours.

## Current Implementation

For each timetable event:

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

## Example

```text
Python       2 hours
DBMS         3 hours
Training     2 hours
---------------------
Total        7 hours
```

Example result:

```json
{
  "faculty_id": 10,
  "allocated_hours": 7
}
```

## Implemented Functions

### Event Duration

`calculate_event_duration()` calculates the duration of a timetable
event in hours.

Invalid time ranges are rejected.

### Faculty Workload

`calculate_faculty_workload()` calculates the total allocated hours for a
specific faculty member.

Events belonging to other faculty members are ignored.

## Current Scope

Implemented:

- Event duration calculation
- Faculty-based event filtering
- Total allocated hours
- Invalid time-range validation

## Not Yet Implemented

The current prototype does not calculate:

- Daily workload
- Weekly workload
- Maximum faculty capacity
- Remaining capacity
- Overloaded status
- Workload balancing
- Automatic workload optimization
- Teaching/training/administrative workload categories

## Future Scope

Future workload optimization can extend the current calculation layer to
support:

- Daily workload analysis
- Weekly workload analysis
- Faculty capacity limits
- Remaining capacity
- Overload detection
- Workload balancing
- Teaching and non-teaching workload categories
- Optimization-based workload distribution

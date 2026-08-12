"""
What-if timetable simulation.

This module allows proposed changes to a timetable event to be evaluated
without modifying the original timetable data.

The simulation:
1. Creates a deep copy of the timetable events.
2. Finds the requested event.
3. Applies the proposed changes to the copied event.
4. Runs conflict detection on the simulated timetable.
5. Returns the simulated event and any resulting conflicts.

The current prototype does not persist changes to the timetable.
"""


from copy import deepcopy

from .conflict_detector import detect_conflicts


def simulate_event_change(events, event_id, changes):
    """
    Simulate changes to a timetable event without modifying the original data.

    Args:
        events: List of timetable event dictionaries.
        event_id: ID of the event to modify in the simulation.
        changes: Dictionary containing fields and values to change.

    Returns:
        Dictionary containing:
            - event_id: ID of the simulated event.
            - simulated_event: Updated event from the copied timetable.
            - conflicts: Conflicts detected after applying the changes.
            - has_conflict: True when at least one conflict exists.

    Raises:
        ValueError: If the requested event does not exist.

    Notes:
        The original events list is not modified.
    """
    simulated_events = deepcopy(events)

    target_event = None

    for event in simulated_events:
        if event["id"] == event_id:
            target_event = event
            break

    if target_event is None:
        raise ValueError(f"Event with id {event_id} was not found.")

    target_event.update(changes)

    conflicts = detect_conflicts(simulated_events)

    return {
        "event_id": event_id,
        "simulated_event": target_event,
        "conflicts": conflicts,
        "has_conflict": len(conflicts) > 0,
    }
"""
Scheduling engine facade.

This module provides a single entry point for common scheduling
operations by delegating work to the specialized scheduling modules.

Current supported operations:
- Timetable conflict detection
- Faculty workload calculation
- Priority value lookup

The facade does not implement scheduling rules itself. It delegates
those responsibilities to the corresponding modules.
"""


from .conflict_detector import detect_conflicts
from .workload_optimizer import calculate_faculty_workload
from .priorities import get_priority_value


class Scheduler:
    """
    Basic scheduling engine facade.

    The Scheduler class stores timetable events and exposes a simplified
    interface for common scheduling operations.
    """

    def __init__(self, events=None):
        """
        Initialize the scheduling engine.

        Args:
            events: Optional list of timetable event dictionaries.
                    Defaults to an empty timetable.
        """
        self.events = events or []

    def detect_conflicts(self):
        """
        Detect conflicts in the scheduler's timetable.

        Returns:
            List of detected faculty, batch, and room conflicts.
        """
        return detect_conflicts(self.events)

    def calculate_faculty_workload(self, faculty_id):
        """
        Calculate workload for a faculty member.

        Args:
            faculty_id: ID of the faculty member.

        Returns:
            Dictionary containing the faculty ID and allocated hours.
        """
        return calculate_faculty_workload(self.events, faculty_id)

    def get_priority_value(self, priority):
        """
        Convert a scheduling priority into its numeric value.

        Args:
            priority: Priority name such as low, normal, high, or urgent.

        Returns:
            Integer priority value.

        Raises:
            ValueError: If the priority is not supported.
        """
        return get_priority_value(priority)
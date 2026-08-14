"""
Application service for scheduling operations.

The SchedulingService coordinates the scheduling engine and exposes
business-level scheduling operations without exposing implementation
details to API routes or other application layers.
"""

from .conflict_detector import detect_conflicts
from .domain import SchedulingEvent
from .workload_optimizer import calculate_faculty_workload


class SchedulingService:
    """
    Application-level scheduling service.

    The service operates on SchedulingEvent objects and delegates the
    actual scheduling logic to specialized scheduling modules.
    """

    def __init__(self, events=None):
        """
        Initialize the scheduling service.

        Args:
            events: Optional list of SchedulingEvent objects.
        """
        self.events = list(events or [])

    def analyze_conflicts(self):
        """
        Analyze the current timetable for scheduling conflicts.

        Returns:
            List of structured conflicts.
        """

        event_data = [event.to_dict() for event in self.events]

        return detect_conflicts(event_data)

    def get_faculty_workload(self, faculty_id):
        """
        Calculate workload for a faculty member.

        Args:
            faculty_id: ID of the faculty member.

        Returns:
            Faculty workload information.
        """

        event_data = [event.to_dict() for event in self.events]

        return calculate_faculty_workload(
            event_data,
            faculty_id,
        )
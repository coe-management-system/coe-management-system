"""
Application service for scheduling operations.

The SchedulingService coordinates the scheduling engine and exposes
business-level scheduling operations without exposing implementation
details to API routes or other application layers.

The service operates on SchedulingEvent objects. Timetable data can be
loaded from the application's real database models through
:meth:`SchedulingService.from_db`.
"""

from .conflict_detector import detect_conflicts, detect_conflicts_structured
from .domain import SchedulingEvent
from .models_timetable import load_timetable_events
from .recommendation import recommend_reschedule as _recommend_reschedule
from .what_if_simulator import simulate_scenario
from .workload_optimizer import (
    calculate_faculty_workload,
    calculate_workload_report,
)


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

    @classmethod
    def from_db(cls, db):
        """
        Build a scheduling service from the real timetable database model.

        Args:
            db: SQLAlchemy session.

        Returns:
            SchedulingService loaded with all TimetableEvent rows.
        """
        events = load_timetable_events(db)

        return cls(events)

    def get_timetable(self):
        """
        Return the timetable as a list of serializable event dictionaries.

        Returns:
            List of timetable event dictionaries.
        """
        return [event.to_dict() for event in self.events]

    def analyze_conflicts(self):
        """
        Analyze the current timetable for scheduling conflicts.

        Returns:
            List of structured conflicts.
        """
        event_data = [event.to_dict() for event in self.events]

        return detect_conflicts(event_data)

    def analyze_conflicts_structured(
        self,
        capacities=None,
        hard_capacities=None,
    ):
        """
        Analyze the timetable through the constraint system.

        Returns:
            List of structured constraint violation dictionaries.
        """
        event_data = [event.to_dict() for event in self.events]

        return detect_conflicts_structured(
            event_data,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

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

    def get_workload_report(self, capacities=None):
        """
        Calculate a workload report for all faculty members.

        Args:
            capacities: Optional mapping of faculty_id to max hours.

        Returns:
            List of faculty workload dictionaries including capacity and
            overload status.
        """
        event_data = [event.to_dict() for event in self.events]

        return calculate_workload_report(event_data, capacities)

    def recommend_reschedule(
        self,
        event_id,
        candidates=None,
        dates=None,
        capacities=None,
        hard_capacities=None,
        preferred_time=None,
    ):
        """
        Generate a rescheduling recommendation for an event.

        Args:
            event_id: ID of the event to reschedule.
            candidates: Optional explicit candidate slots.
            dates: Optional dates to generate candidates across.
            capacities: Optional faculty workload capacities.
            hard_capacities: Optional absolute workload capacities.
            preferred_time: Optional preferred start time.

        Returns:
            Recommendation dictionary. See recommendation module.
        """
        event_data = [event.to_dict() for event in self.events]

        return _recommend_reschedule(
            event_data,
            event_id,
            candidates=candidates,
            dates=dates,
            capacities=capacities,
            hard_capacities=hard_capacities,
            preferred_time=preferred_time,
        )

    def run_what_if(
        self,
        scenario,
        capacities=None,
        hard_capacities=None,
    ):
        """
        Evaluate a what-if scenario without modifying the timetable.

        Args:
            scenario: Scenario dictionary. See what_if_simulator module.
            capacities: Optional faculty workload capacities.
            hard_capacities: Optional absolute workload capacities.

        Returns:
            Scenario evaluation dictionary.
        """
        event_data = [event.to_dict() for event in self.events]

        return simulate_scenario(
            event_data,
            scenario,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )
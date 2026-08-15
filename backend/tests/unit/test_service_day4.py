import unittest
from datetime import date

from app.scheduling.domain import SchedulingEvent
from app.scheduling.optimizer import OptimizationConfig
from app.scheduling.service import SchedulingService


def make_event(
    event_id,
    faculty_id,
    batch_id,
    room_id,
    start,
    end,
    priority=2,
):
    return SchedulingEvent(
        id=event_id,
        subject_id=101,
        faculty_id=faculty_id,
        batch_id=batch_id,
        room_id=room_id,
        date=date(2026, 8, 15),
        start_time=start,
        end_time=end,
        priority=priority,
    )


class TestSchedulingServiceOptimize(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]
        self.service = SchedulingService(self.events)

    def test_optimize_returns_structured_result(self):
        result = self.service.optimize()

        self.assertEqual(result["status"], "OPTIMIZED")
        self.assertEqual(result["conflicts_before"], 1)
        self.assertEqual(result["conflicts_after"], 0)
        self.assertIn("comparison", result)
        self.assertIn("objective_breakdown", result)
        self.assertEqual(result["comparison"]["events"]["total"], 2)
        self.assertEqual(result["comparison"]["events"]["moved"], 1)

    def test_optimize_with_capacities(self):
        result = self.service.optimize(
            capacities={10: 6},
        )

        self.assertIn("workload_before", result)
        self.assertIn("workload_after", result)
        self.assertEqual(result["workload_before"]["faculty"][0]["faculty_id"], 10)

    def test_optimize_with_config_mode(self):
        result = self.service.optimize(
            config=OptimizationConfig(
                mode="CONFLICT_MINIMIZATION",
            )
        )

        self.assertEqual(result["conflicts_after"], 0)

    def test_optimize_does_not_modify_service_events(self):
        snapshot = [e.to_dict() for e in self.service.events]

        self.service.optimize()

        self.assertEqual(
            snapshot,
            [e.to_dict() for e in self.service.events],
        )


if __name__ == "__main__":
    unittest.main()

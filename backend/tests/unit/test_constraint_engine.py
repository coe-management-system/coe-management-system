import unittest

from app.scheduling.constraint_engine import (
    ConstraintEngine,
    FACULTY_CONSTRAINT,
    GROUP_CONSTRAINT,
    ROOM_CONSTRAINT,
    BATCH_CONSTRAINT,
    TIME_CONSTRAINT,
    WORKLOAD_CONSTRAINT,
    HARD,
    SOFT,
)


def make_event(
    event_id,
    faculty_id,
    batch_id,
    room_id="101",
    date="2026-08-15",
    start_time="10:00",
    end_time="11:00",
    priority=2,
    group_id=None,
):
    return {
        "id": event_id,
        "subject_id": 1,
        "faculty_id": faculty_id,
        "batch_id": batch_id,
        "room_id": room_id,
        "group_id": group_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "priority": priority,
    }


class TestConstraintEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ConstraintEngine()

    def test_faculty_conflict(self):
        events = [
            make_event(1, 10, 201),
            make_event(2, 10, 202),
        ]

        violations = self.engine.evaluate(events)

        faculty_violations = [
            v for v in violations
            if v.constraint_type == FACULTY_CONSTRAINT
        ]

        self.assertEqual(len(faculty_violations), 1)
        self.assertEqual(faculty_violations[0].severity, HARD)
        self.assertEqual(faculty_violations[0].conflicting_event_id, 2)
        self.assertEqual(faculty_violations[0].resource, 10)

    def test_batch_conflict(self):
        events = [
            make_event(1, 10, 201),
            make_event(2, 11, 201),
        ]

        violations = self.engine.evaluate(events)

        batch_violations = [
            v for v in violations
            if v.constraint_type == BATCH_CONSTRAINT
        ]

        self.assertEqual(len(batch_violations), 1)
        self.assertEqual(batch_violations[0].resource, 201)

    def test_group_conflict(self):
        events = [
            make_event(1, 10, 201, group_id=301),
            make_event(2, 11, 202, group_id=301),
        ]

        violations = self.engine.evaluate(events)

        group_violations = [
            v for v in violations
            if v.constraint_type == GROUP_CONSTRAINT
        ]

        self.assertEqual(len(group_violations), 1)
        self.assertEqual(group_violations[0].resource, 301)

    def test_room_conflict(self):
        events = [
            make_event(1, 10, 201, room_id="LAB-101"),
            make_event(2, 11, 202, room_id="LAB-101"),
        ]

        violations = self.engine.evaluate(events)

        room_violations = [
            v for v in violations
            if v.constraint_type == ROOM_CONSTRAINT
        ]

        self.assertEqual(len(room_violations), 1)
        self.assertEqual(room_violations[0].resource, "LAB-101")
        self.assertIn("LAB-101", room_violations[0].message)

    def test_invalid_time(self):
        event = make_event(1, 10, 201, start_time="12:00", end_time="10:00")

        violations = self.engine.evaluate([event])

        time_violations = [
            v for v in violations
            if v.constraint_type == TIME_CONSTRAINT
        ]

        self.assertEqual(len(time_violations), 1)
        self.assertEqual(time_violations[0].severity, HARD)

    def test_adjacent_events_no_conflict(self):
        events = [
            make_event(1, 10, 201, start_time="10:00", end_time="11:00"),
            make_event(2, 10, 201, start_time="11:00", end_time="12:00"),
        ]

        violations = self.engine.evaluate(events)

        self.assertEqual(violations, [])

    def test_different_date_no_conflict(self):
        events = [
            make_event(1, 10, 201, date="2026-08-15"),
            make_event(2, 10, 201, date="2026-08-16"),
        ]

        violations = self.engine.evaluate(events)

        self.assertEqual(violations, [])

    def test_overlap_variations(self):
        faculty = 10
        batch = 201

        overlaps = [
            ("10:00", "11:00", "10:30", "11:30"),
            ("10:00", "12:00", "10:30", "11:00"),
            ("10:30", "11:00", "10:00", "12:00"),
            ("10:00", "11:00", "10:00", "11:00"),
            ("10:00", "11:00", "10:00", "10:30"),
            ("10:00", "11:00", "10:59", "12:00"),
        ]

        for start_a, end_a, start_b, end_b in overlaps:
            with self.subTest(start_a=start_a, end_a=end_a, start_b=start_b, end_b=end_b):
                events = [
                    make_event(1, faculty, batch, start_time=start_a, end_time=end_a),
                    make_event(2, faculty, batch, start_time=start_b, end_time=end_b),
                ]

                violations = self.engine.evaluate(events)

                self.assertTrue(
                    any(v.constraint_type == FACULTY_CONSTRAINT for v in violations),
                    f"Expected conflict for {start_a}-{end_a} vs {start_b}-{end_b}",
                )

    def test_non_overlap_not_conflict(self):
        events = [
            make_event(1, 10, 201, start_time="10:00", end_time="11:00"),
            make_event(2, 10, 201, start_time="11:00", end_time="12:00"),
        ]

        violations = self.engine.evaluate(events)

        self.assertEqual(violations, [])

    def test_multiple_simultaneous_conflicts(self):
        events = [
            make_event(1, 10, 201, room_id="101"),
            make_event(2, 10, 201, room_id="101"),
        ]

        violations = self.engine.evaluate(events)

        types = {v.constraint_type for v in violations}

        self.assertTrue(FACULTY_CONSTRAINT in types)
        self.assertTrue(BATCH_CONSTRAINT in types)
        self.assertTrue(ROOM_CONSTRAINT in types)

    def test_structured_detection_has_required_fields(self):
        from app.scheduling.conflict_detector import detect_conflicts_structured

        events = [
            make_event(1, 10, 201, room_id="101"),
            make_event(2, 10, 201, room_id="101"),
        ]

        violations = detect_conflicts_structured(events)

        self.assertEqual(len(violations), 3)

        for violation in violations:
            self.assertIn("constraint_type", violation)
            self.assertIn("severity", violation)
            self.assertIn("event_id", violation)
            self.assertIn("conflicting_event_id", violation)
            self.assertIn("resource", violation)
            self.assertIn("message", violation)


class TestWorkloadConstraint(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(1, 10, 201, start_time="09:00", end_time="11:00"),
        ]

    def _candidate(self, faculty_id=10, start="11:00", end="12:00", event_id=None):
        candidate = {
            "event_id": event_id,
            "faculty_id": faculty_id,
            "batch_id": 201,
            "room_id": "101",
            "date": "2026-08-15",
            "start_time": start,
            "end_time": end,
        }
        if event_id is None:
            candidate.pop("event_id")
        return candidate

    def test_normal_workload(self):
        engine = ConstraintEngine(capacities={10: 6})

        violations = engine.evaluate_candidate(self.events, self._candidate())

        workload_violations = [
            v for v in violations
            if v.constraint_type == WORKLOAD_CONSTRAINT
        ]

        self.assertEqual(workload_violations, [])

    def test_workload_at_capacity(self):
        engine = ConstraintEngine(capacities={10: 3})

        violations = engine.evaluate_candidate(self.events, self._candidate())

        self.assertEqual(violations, [])

    def test_overloaded_faculty_soft_when_within_hard(self):
        engine = ConstraintEngine(
            capacities={10: 2},
            hard_capacities={10: 5},
        )

        violations = engine.evaluate_candidate(self.events, self._candidate())

        workload_violations = [
            v for v in violations
            if v.constraint_type == WORKLOAD_CONSTRAINT
        ]

        self.assertEqual(len(workload_violations), 1)
        self.assertEqual(workload_violations[0].severity, SOFT)

    def test_candidate_increases_workload(self):
        engine = ConstraintEngine(capacities={10: 3}, hard_capacities={10: 4})

        before = engine.evaluate_candidate(
            self.events,
            self._candidate(start="11:00", end="12:00"),
        )

        increase = engine.evaluate_candidate(
            self.events,
            self._candidate(start="11:00", end="13:00"),
        )

        self.assertEqual(
            len([v for v in before if v.constraint_type == WORKLOAD_CONSTRAINT]),
            0,
        )
        self.assertEqual(
            len([v for v in increase if v.constraint_type == WORKLOAD_CONSTRAINT]),
            1,
        )

    def test_candidate_exceeding_hard_capacity_rejected(self):
        engine = ConstraintEngine(capacities={10: 2}, hard_capacities={10: 2})

        violations = engine.evaluate_candidate(self.events, self._candidate())

        workload_violations = [
            v for v in violations
            if v.constraint_type == WORKLOAD_CONSTRAINT
        ]

        self.assertEqual(len(workload_violations), 1)
        self.assertEqual(workload_violations[0].severity, HARD)


if __name__ == "__main__":
    unittest.main()
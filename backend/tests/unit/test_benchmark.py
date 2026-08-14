import unittest

from app.scheduling.benchmark import build_benchmark_scenario, run_benchmark


class TestBenchmark(unittest.TestCase):

    def test_scenario_is_reproducible(self):
        first = build_benchmark_scenario()
        second = build_benchmark_scenario()

        self.assertEqual(first, second)

    def test_scenario_contains_metadata(self):
        scenario = build_benchmark_scenario()

        meta = scenario["meta"]

        self.assertIn("number_of_events", meta)
        self.assertIn("number_of_faculty", meta)
        self.assertIn("number_of_rooms", meta)
        self.assertIn("number_of_batches_groups", meta)
        self.assertEqual(meta["number_of_events"], len(scenario["events"]))

    def test_benchmark_records_metrics(self):
        result = run_benchmark()

        self.assertIn("scenario", result)
        self.assertIn("initial_conflicts", result)
        self.assertIn("final_conflicts", result)
        self.assertIn("overloaded_faculty", result)
        self.assertIn("moved_events", result)
        self.assertIn("execution_time_seconds", result)
        self.assertIn("recommendation_status", result)

    def test_benchmark_is_deterministic(self):
        first = run_benchmark()
        second = run_benchmark()

        self.assertEqual(
            first["initial_conflicts"],
            second["initial_conflicts"],
        )
        self.assertEqual(
            first["final_conflicts"],
            second["final_conflicts"],
        )

    def test_benchmark_does_not_move_events(self):
        result = run_benchmark()

        self.assertEqual(result["moved_events"], 0)
        self.assertEqual(
            result["initial_conflicts"],
            result["final_conflicts"],
        )


if __name__ == "__main__":
    unittest.main()
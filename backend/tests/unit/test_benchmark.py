import unittest

from app.scheduling.benchmark import (
    build_benchmark_scenario,
    build_optimization_scenario,
    run_benchmark,
    run_optimization_benchmark,
    run_performance_benchmark,
    run_rnd_evaluation,
    run_rnd_evaluation_suite,
)


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

    def test_optimization_scenario_is_reproducible(self):
        first = build_optimization_scenario()
        second = build_optimization_scenario()

        self.assertEqual(first, second)

    def test_optimization_benchmark_records_metrics(self):
        result = run_optimization_benchmark()

        self.assertIn("scenario", result)
        self.assertIn("status", result)
        self.assertIn("conflicts", result)
        self.assertIn("workload", result)
        self.assertIn("objective_score", result)
        self.assertIn("moved_events", result)
        self.assertIn("execution_time_seconds", result)

    def test_optimization_benchmark_resolves_conflicts(self):
        result = run_optimization_benchmark()

        self.assertEqual(result["conflicts"]["before"], 2)
        self.assertEqual(result["conflicts"]["after"], 0)

    def test_optimization_benchmark_is_deterministic(self):
        first = run_optimization_benchmark()
        second = run_optimization_benchmark()

        self.assertEqual(first["status"], second["status"])
        self.assertEqual(
            first["objective_score"],
            second["objective_score"],
        )
        self.assertEqual(first["moved_events"], second["moved_events"])

    def test_performance_benchmark_records_sizes(self):
        results = run_performance_benchmark(sizes=(10,))

        self.assertIn(10, results)
        self.assertIn("input_size", results[10])
        self.assertIn("execution_time_seconds", results[10])
        self.assertIn("result_quality", results[10])

    def test_rnd_evaluation_compares_all_approaches(self):
        result = run_rnd_evaluation()

        self.assertEqual(
            set(result["approaches"].keys()),
            {"greedy_baseline", "constraint_based", "optimization"},
        )
        self.assertIn("best_approach", result["comparison"])
        self.assertIn("syllabus_delay_estimate", result)

    def test_rnd_evaluation_suite_handles_synthetic_scenarios(self):
        results = run_rnd_evaluation_suite(sizes=(10,))

        self.assertIn(10, results)
        entry = results[10]
        self.assertEqual(
            set(entry["avg_execution_time_seconds"].keys()),
            {"greedy_baseline", "constraint_based", "optimization"},
        )
        self.assertEqual(len(entry["detailed_runs"]), 3)


if __name__ == "__main__":
    unittest.main()
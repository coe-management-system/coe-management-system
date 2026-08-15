import unittest

from app.scheduling.scoring import score_candidate, rank_candidates


class TestScoring(unittest.TestCase):

    def test_feasible_no_penalty_candidate_scores_high(self):
        candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }

        result = score_candidate(candidate, workload_impact={"status": "optimal"})

        self.assertEqual(result["penalty"], 0.0)
        self.assertEqual(result["score"], 1000.0)
        self.assertEqual(result["breakdown"], {})

    def test_workload_overload_is_penalised(self):
        candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }

        clean = score_candidate(
            candidate,
            workload_impact={"status": "optimal"},
        )

        overloaded = score_candidate(
            candidate,
            workload_impact={"status": "overloaded"},
        )

        self.assertGreater(clean["score"], overloaded["score"])

    def test_soft_violation_is_penalised(self):
        clean_candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }
        soft_candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [{"severity": "soft"}],
        }

        clean = score_candidate(
            clean_candidate,
            workload_impact={"status": "optimal"},
        )

        soft = score_candidate(
            soft_candidate,
            workload_impact={"status": "optimal"},
        )

        self.assertLess(soft["score"], clean["score"])

    def test_high_priority_event_costs_more(self):
        candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }

        low = score_candidate(candidate, priority="low")
        urgent = score_candidate(candidate, priority="urgent")

        self.assertGreater(low["score"], urgent["score"])

    def test_candidate_a_preferred_over_overloading_candidate_b(self):
        # Candidate A: no conflicts, no overload.
        candidate_a = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }

        # Candidate B: no hard conflict but creates workload overload.
        candidate_b = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [{"severity": "soft"}],
        }

        score_a = score_candidate(
            candidate_a,
            workload_impact={"status": "optimal"},
            priority="normal",
        )
        score_b = score_candidate(
            candidate_b,
            workload_impact={"status": "overloaded"},
            priority="normal",
        )

        ranked = rank_candidates(
            [
                {**candidate_b, "score_info": score_b},
                {**candidate_a, "score_info": score_a},
            ]
        )

        self.assertEqual(ranked[0]["score_info"]["score"], score_a["score"])
        self.assertEqual(ranked[1]["score_info"]["score"], score_b["score"])

    def test_ranking_is_deterministic(self):
        candidate = {
            "date": "2026-08-15",
            "start_time": "14:00",
            "end_time": "15:00",
            "violations": [],
        }

        scores = {
            "a": score_candidate(candidate, priority="low"),
            "b": score_candidate(candidate, priority="normal"),
            "c": score_candidate(candidate, priority="high"),
        }

        first = rank_candidates(
            [
                {**candidate, "score_info": scores["a"]},
                {**candidate, "score_info": scores["b"]},
                {**candidate, "score_info": scores["c"]},
            ]
        )
        second = rank_candidates(
            [
                {**candidate, "score_info": scores["a"]},
                {**candidate, "score_info": scores["b"]},
                {**candidate, "score_info": scores["c"]},
            ]
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
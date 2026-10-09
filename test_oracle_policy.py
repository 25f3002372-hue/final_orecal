import unittest

from oracle_policy import (
    choose_clarifications,
    maximum_weight_matching,
    parse_candidate_pairs,
    run_oracle,
    valid_probability,
)


class TestOraclePolicy(unittest.TestCase):

    def test_probability_validation(self):
        self.assertEqual(valid_probability(0.75), 0.75)
        self.assertEqual(valid_probability(-0.1), 0.0)
        self.assertEqual(valid_probability(1.5), 0.0)
        self.assertEqual(valid_probability("invalid"), 0.0)
        self.assertEqual(valid_probability(float("nan")), 0.0)

    def test_duplicate_pairs_are_removed(self):
        rows = [
            {
                "person_a": "A",
                "person_b": "B",
                "p_msmi": 0.4,
                "feasible": True,
            },
            {
                "person_a": "B",
                "person_b": "A",
                "p_msmi": 0.8,
                "feasible": True,
            },
        ]

        pairs = parse_candidate_pairs(rows)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["p_msmi"], 0.8)

    def test_self_match_is_rejected(self):
        rows = [
            {
                "person_a": "A",
                "person_b": "A",
                "p_msmi": 0.9,
                "feasible": True,
            }
        ]

        self.assertEqual(parse_candidate_pairs(rows), [])

    def test_clarifications_respect_budget(self):
        questions = [
            {
                "question_id": "hard",
                "cost": 3,
                "expected_gain": 0.3,
                "resolves_hard_constraint": True,
            },
            {
                "question_id": "soft",
                "cost": 1,
                "expected_gain": 0.1,
                "resolves_hard_constraint": False,
            },
        ]

        selected, spent = choose_clarifications(questions, budget=3)

        self.assertLessEqual(spent, 3)
        self.assertEqual(spent, sum(q["cost"] for q in selected))
        self.assertEqual(selected[0]["question_id"], "hard")

    def test_matching_respects_feasibility(self):
        pairs = [
            {
                "person_a": "A",
                "person_b": "B",
                "p_msmi": 0.9,
                "feasible": False,
            },
            {
                "person_a": "A",
                "person_b": "C",
                "p_msmi": 0.7,
                "feasible": True,
            },
        ]

        matching = maximum_weight_matching(pairs)

        self.assertEqual(len(matching), 1)
        self.assertEqual(
            {matching[0]["person_a"], matching[0]["person_b"]},
            {"A", "C"},
        )

    def test_person_appears_at_most_once(self):
        pairs = [
            {
                "person_a": "A",
                "person_b": "B",
                "p_msmi": 0.9,
                "feasible": True,
            },
            {
                "person_a": "A",
                "person_b": "C",
                "p_msmi": 0.8,
                "feasible": True,
            },
            {
                "person_a": "B",
                "person_b": "D",
                "p_msmi": 0.8,
                "feasible": True,
            },
        ]

        matching = maximum_weight_matching(pairs)
        people = [
            person
            for pair in matching
            for person in (pair["person_a"], pair["person_b"])
        ]

        self.assertEqual(len(people), len(set(people)))

    def test_run_oracle_output_shape(self):
        state = {
            "clarification_budget": 0,
            "clarification_questions": [],
            "candidate_pairs": [
                {
                    "person_a": "A",
                    "person_b": "B",
                    "p_msmi": 0.8,
                    "feasible": True,
                }
            ],
        }

        result = run_oracle(state)

        self.assertIn("clarifications", result)
        self.assertIn("clarification_units_used", result)
        self.assertIn("pairs", result)
        self.assertEqual(result["clarification_units_used"], 0)
        self.assertEqual(len(result["pairs"]), 1)


if __name__ == "__main__":
    unittest.main()

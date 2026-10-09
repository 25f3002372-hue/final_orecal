"""
ORACLE: Opportunity-Aware Reciprocal Allocation with Learning
and Confidence Estimation.

Framework-neutral starter policy.

Expected candidate-pair fields:
    person_a: str
    person_b: str
    p_msmi: float, between 0 and 1
    feasible: bool

Expected clarification-question fields:
    question_id: str
    cost: int
    expected_gain: float
    resolves_hard_constraint: bool

NOTE:
This input/output contract is a prototype contract, not the official
hackathon simulator contract. Adapt the adapter after inspecting the
competition starter kit.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Mapping

DEFAULT_CLARIFICATION_BUDGET = 12
HARD_BUNDLE_COST = 3
SOFT_FIELD_COST = 1


def valid_probability(value: Any) -> float:
    """Return a valid probability; malformed values become zero."""
    try:
        probability = float(value)
    except (TypeError, ValueError):
        return 0.0

    if not isfinite(probability):
        return 0.0

    if not 0.0 <= probability <= 1.0:
        return 0.0

    return probability


def normalize_pair(a: str, b: str) -> tuple[str, str]:
    """Give an unordered pair a stable key."""
    return tuple(sorted((a, b)))


def parse_candidate_pairs(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate candidate pairs and remove duplicate unordered pairs.

    If duplicates exist, retain the row with the highest probability.
    A pair is considered feasible only when its 'feasible' value is True.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}

    for row in rows:
        a = row.get("person_a")
        b = row.get("person_b")

        if not isinstance(a, str) or not a.strip():
            continue
        if not isinstance(b, str) or not b.strip():
            continue
        if a == b:
            continue

        probability = valid_probability(row.get("p_msmi"))
        feasible = row.get("feasible") is True

        candidate = {
            "person_a": a,
            "person_b": b,
            "p_msmi": probability,
            "feasible": feasible,
        }

        key = normalize_pair(a, b)
        existing = best.get(key)

        if existing is None or probability > existing["p_msmi"]:
            best[key] = candidate

    return list(best.values())


def choose_clarifications(
    questions: Iterable[Mapping[str, Any]],
    budget: int = DEFAULT_CLARIFICATION_BUDGET,
) -> tuple[list[dict[str, Any]], int]:
    """
    Select clarification questions under a unit budget.

    Questions marked as resolving a hard constraint are considered first.
    Within each category, questions are ranked by expected_gain / cost.

    expected_gain must be provided by the caller. This function does not
    calculate expected value of information itself.
    """
    try:
        remaining = max(0, int(budget))
    except (TypeError, ValueError):
        remaining = DEFAULT_CLARIFICATION_BUDGET

    prepared: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for raw in questions:
        question_id = raw.get("question_id")

        if not isinstance(question_id, str) or not question_id:
            continue
        if question_id in seen_ids:
            continue

        seen_ids.add(question_id)

        resolves_hard = raw.get("resolves_hard_constraint") is True
        default_cost = (
            HARD_BUNDLE_COST if resolves_hard else SOFT_FIELD_COST
        )

        try:
            cost = int(raw.get("cost", default_cost))
            gain = float(raw.get("expected_gain", 0.0))
        except (TypeError, ValueError):
            continue

        if cost <= 0 or not isfinite(gain) or gain <= 0:
            continue

        prepared.append({
            **dict(raw),
            "question_id": question_id,
            "cost": cost,
            "expected_gain": gain,
            "resolves_hard_constraint": resolves_hard,
        })

    prepared.sort(
        key=lambda q: (
            not q["resolves_hard_constraint"],
            -(q["expected_gain"] / q["cost"]),
            -q["expected_gain"],
            q["question_id"],
        )
    )

    selected: list[dict[str, Any]] = []
    spent = 0

    for question in prepared:
        if question["cost"] <= remaining:
            selected.append(question)
            remaining -= question["cost"]
            spent += question["cost"]

    return selected, spent


def maximum_weight_matching(
    candidate_pairs: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    Find a one-to-one matching maximizing the sum of pair probabilities.

    Infeasible pairs and pairs with zero probability are excluded.
    Requires NetworkX: pip install -r requirements.txt
    """
    try:
        import networkx as nx
    except ImportError as exc:
        raise RuntimeError(
            "NetworkX is required. Run: pip install -r requirements.txt"
        ) from exc

    graph = nx.Graph()
    pair_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for pair in candidate_pairs:
        if pair.get("feasible") is not True:
            continue

        probability = valid_probability(pair.get("p_msmi"))
        if probability <= 0:
            continue

        a = pair.get("person_a")
        b = pair.get("person_b")

        if not isinstance(a, str) or not a:
            continue
        if not isinstance(b, str) or not b or a == b:
            continue

        key = normalize_pair(a, b)

        normalized = {
            "person_a": key[0],
            "person_b": key[1],
            "p_msmi": probability,
            "feasible": True,
        }

        existing = pair_by_key.get(key)
        if existing is None or probability > existing["p_msmi"]:
            pair_by_key[key] = normalized

    for (a, b), pair in pair_by_key.items():
        graph.add_edge(a, b, weight=pair["p_msmi"])

    matching = nx.max_weight_matching(
        graph,
        maxcardinality=False,
        weight="weight",
    )

    result = []
    for a, b in matching:
        key = normalize_pair(a, b)
        if key in pair_by_key:
            result.append(pair_by_key[key])

    result.sort(key=lambda pair: (pair["person_a"], pair["person_b"]))
    return result


def run_oracle(state: Mapping[str, Any]) -> dict[str, Any]:
    """
    Run ORACLE using the prototype state schema.

    Expected state:
    {
        "clarification_budget": 12,
        "clarification_questions": [...],
        "candidate_pairs": [...]
    }

    The function returns selected clarification IDs and matched pairs.
    """
    budget = state.get(
        "clarification_budget",
        DEFAULT_CLARIFICATION_BUDGET,
    )

    questions = state.get("clarification_questions", [])
    if not isinstance(questions, list):
        questions = []

    selected_questions, units_used = choose_clarifications(
        questions,
        budget,
    )

    rows = state.get("candidate_pairs", [])
    if not isinstance(rows, list):
        rows = []

    parsed_pairs = parse_candidate_pairs(rows)
    matched_pairs = maximum_weight_matching(parsed_pairs)

    return {
        "clarifications": [
            question["question_id"]
            for question in selected_questions
        ],
        "clarification_units_used": units_used,
        "pairs": [
            {
                "person_a": pair["person_a"],
                "person_b": pair["person_b"],
                "p_msmi": pair["p_msmi"],
            }
            for pair in matched_pairs
        ],
    }


if __name__ == "__main__":
    # Small illustrative example; these are not benchmark results.
    example_state = {
        "clarification_budget": 4,
        "clarification_questions": [
            {
                "question_id": "q_hard_1",
                "cost": 3,
                "expected_gain": 0.20,
                "resolves_hard_constraint": True,
            },
            {
                "question_id": "q_soft_1",
                "cost": 1,
                "expected_gain": 0.05,
                "resolves_hard_constraint": False,
            },
        ],
        "candidate_pairs": [
            {
                "person_a": "A",
                "person_b": "B",
                "p_msmi": 0.80,
                "feasible": True,
            },
            {
                "person_a": "A",
                "person_b": "C",
                "p_msmi": 0.60,
                "feasible": True,
            },
            {
                "person_a": "B",
                "person_b": "C",
                "p_msmi": 0.70,
                "feasible": True,
            },
        ],
    }

    print(run_oracle(example_state))

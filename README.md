
# ORACLE — Reciprocal Matching Policy

**ORACLE** stands for Opportunity-Aware Reciprocal Allocation with Learning and Confidence Estimation.

This repository contains a framework-neutral prototype for reciprocal matching with hard feasibility constraints, clarification-budget allocation, and maximum-weight matching.

> **Status:** Prototype. The official hackathon simulator interface, required entry point, and evaluation results have not yet been verified.

## Features

- Probability validation and duplicate-pair removal.
- Hard feasibility filtering before matching.
- Clarification selection under a limited budget.
- Maximum-weight one-to-one matching.
- Unit tests for core policy behavior.

## Project structure

```text
orecal_labs_by_the-_legends/
├── README.md
├── oracle_policy.py
├── requirements.txt
└── test_oracle_policy.py
```

## Requirements

- Python 3.10 or newer recommended.
- NetworkX 3.x.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the example

```bash
python oracle_policy.py
```

The example prints a result using illustrative data. It is not a competition score or benchmark.

## Run tests

```bash
python -m unittest -v
```

## Prototype input format

The `run_oracle()` function accepts a dictionary with this structure:

```python
state = {
    "clarification_budget": 12,
    "clarification_questions": [
        {
            "question_id": "question_1",
            "cost": 3,
            "expected_gain": 0.2,
            "resolves_hard_constraint": True
        }
    ],
    "candidate_pairs": [
        {
            "person_a": "A",
            "person_b": "B",
            "p_msmi": 0.8,
            "feasible": True
        }
    ]
}
```

Example usage:

```python
from oracle_policy import run_oracle

result = run_oracle(state)
print(result)
```

## How the policy works

### 1. Candidate validation

Candidate pairs are checked for valid identifiers and probabilities. Duplicate unordered pairs are removed.

### 2. Feasibility

Pairs marked as infeasible are excluded from the matching graph. The simulator or upstream policy must provide the correct feasibility values.

### 3. Clarifications

Questions are ranked using the supplied expected gain per unit cost. Questions resolving hard constraints are prioritized.

The current prototype does **not** calculate expected value of information itself. That requires a model of how answers change feasible pairs and expected outcomes.

### 4. Matching

NetworkX maximum-weight matching chooses disjoint pairs to maximize the sum of supplied `p_msmi` values.

### 5. Output

The prototype returns selected clarification IDs, budget usage, and matched pairs.

## Important limitations

This implementation is not yet a complete learned matching system.

- `p_msmi` is supplied as input; this repository does not train a predictive model.
- Expected clarification gains are supplied as input; they are not estimated by the policy.
- The generic `run_oracle()` schema may not match the official competition interface.
- Delayed feedback, cold-start learning, shifting populations, and outcome-weight adaptation are not implemented.
- No official evaluator or benchmark has been run.

## Next steps for the hackathon

1. Add the official simulator starter kit and inspect its exact input/output contract.
2. Implement the required competition entry point.
3. Train and validate a reciprocal-outcome prediction model using permitted observations.
4. Estimate clarification value by measuring expected changes in the matching objective.
5. Integrate the official baseline policies.
6. Run the official evaluator across every required scenario.
7. Report measured results and ablation studies without inventing scores.

## License

Add the license required by your team or competition.

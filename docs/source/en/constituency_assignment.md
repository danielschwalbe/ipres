# Constituency Assignment

In the final step of the evaluation, each constituency is assigned to exactly one party for representation. The guiding principle: a constituency should be represented by the party for which it is most important relative to that party's other constituencies.

---

## Relative Importance

First, an **importance** value is calculated for every combination of constituency and party. It expresses how strongly a constituency contributes to a party's vote share compared to the party's other constituencies.

Let `r_ij` be the vote share of party `j` in constituency `i` (relative to all votes cast in that constituency). Then:

```
w_ij = (M − 1) · r_ij / Σ(r_kj  for all k ≠ i)
```

The `(M−1)` normalisation ensures that a uniform vote distribution yields `w = 1.0` everywhere:

- `w > 1.0` → constituency is above-average important for this party
- `w < 1.0` → below-average important
- `w = 1.0` → average

**Example** (5 constituencies, parties A / B / C):

| Constituency | A    | B    | C    |
|--------------|------|------|------|
| C1           | 1.22 | 0.70 | 0.73 |
| C2           | 0.80 | 1.40 | 1.20 |
| C3           | 0.90 | 0.91 | 1.78 |
| C4           | 1.11 | 0.91 | 0.73 |
| C5           | 1.00 | 1.14 | 0.73 |

A is strongest in C1, B in C2, C in C3. With quotas A: 3, B: 2, C: 0 the result is `{C1: A, C2: B, C3: A, C4: A, C5: B}`.

---

## Allocation Methods

Three methods are available to derive an assignment from the importance matrix and the per-party constituency counts:

| Method | Description |
|---|---|
| `OPTIMAL` *(default)* | Hungarian algorithm (Kuhn-Munkres). Finds the assignment that provably maximises the total importance score. More computationally intensive, but globally optimal. |
| `GREEDY` | Iteratively assigns the (constituency, party) pair with the highest importance, as long as the party's quota has not yet been exhausted. Fast, but not globally optimal. |
| `STABLE_MATCHING` | Gale-Shapley algorithm (stable matching). No constituency-party pair would simultaneously prefer a different assignment. |

---

## Effect of `constituency_representation`

- **`ENTIRE_PARLIAMENT`** *(default)*: Importance is computed from the votes of all parties.
- **`GOVERNING_MAJORITY`**: Only the votes of the governing parties are used to compute importance.

---

## Configuration Parameters

| Parameter | Class | Description |
|---|---|---|
| `constituency_allocation_method` | `ElectionEvaluator` | Allocation method (default: `OPTIMAL`) |
| `constituency_representation` | `ElectionConfig` + `ElectionEvaluator` | Basis for importance calculation |

---

## Execution in the Simulation

The class [`ConstituencyAssigner`](../../src/ipres/constituency_assigner.py) performs this step. It takes the constituency count allocation result as input.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, ConstituencyCountDeterminer, ConstituencyAssigner,
                   SuperMajorityMargin, MarginUnit)
import pandas as pd

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'constituency_size': [100_000] * 5,
}))
config = ElectionConfig(
    constituencies_config=cc,
    participating_parties=['A', 'B', 'C'],
    parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
    seed=42,
)

election = Election(electionConfig=config)
votes = {
    'C1': {'A': 70, 'B': 20, 'C': 10},
    'C2': {'A': 50, 'B': 35, 'C': 15},
    'C3': {'A': 55, 'B': 25, 'C': 20},
    'C4': {'A': 65, 'B': 25, 'C': 10},
    'C5': {'A': 60, 'B': 30, 'C': 10},
}
election.start(votes=votes)

seats  = SeatDistributor().run(election)                    # {'A': 6, 'B': 3, 'C': 1}
counts = ConstituencyCountDeterminer().run(election, seats)  # {'A': 3, 'B': 2, 'C': 0}
assignment = ConstituencyAssigner(seed=42).run(election, counts)
print(assignment)  # {'C1': 'A', 'C2': 'B', 'C3': 'A', 'C4': 'A', 'C5': 'B'}
```
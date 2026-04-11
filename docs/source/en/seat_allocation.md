# Seat Allocation

Once the iterative proportional election is complete, parliamentary seats are distributed among the parties. The procedure distinguishes two cases.

---

## Case 1 — Winner Receives an Assigned Majority

**Condition:** The winning party (or coalition) did *not* reach the parliament majority threshold by directly exceeding it in the final round. This applies when:

- the winner was determined through party elimination across multiple rounds or by drawing of lots, **or**
- the winner exceeded the ballot threshold (e.g. 52 %) but falls below the parliament majority threshold (e.g. 55 %).

**Procedure:**

1. The winner receives exactly as many seats as are required for a parliament majority (retrievable via `ElectionConfig.getParliamentMajoritySeats()`).
2. The remaining seats are distributed proportionally among the **other parties** — based on their vote shares in the **first round** (before any coalition formation or party elimination).

The first-round result is used because it most directly reflects the will of the voters: all parties were still competing, and no voter had to vote tactically.

---

## Case 2 — Proportional Distribution of All Seats

**Condition:** The winner exceeded the parliament majority threshold through a clear victory in the final round.

**Procedure:** All parliamentary seats are distributed proportionally according to the result of the **final round**. Coalition votes are counted together.

---

## Coalitions

If a coalition has won seats, these are — after the overall allocation — distributed proportionally among the coalition members. The weights used are the member parties' vote weights from the round in which the coalition was formed.

---

## Seat Distribution Method

Seats are indivisible. A purely proportional calculation typically yields fractional numbers (e.g. "Party A deserves 12.7 seats"), which must be rounded to whole numbers without changing the total. Different rounding methods treat these fractions differently and tend to favour either larger or smaller parties. Such a method is called an apportionment method.

For proportional allocation (both of the total seats and within coalitions), an apportionment method is applied. The method is configured via the `seat_distribution_method` parameter in [`ElectionEvaluator`](../../../src/ipres/election_evaluator.py). The available options are:

| Method | Description |
|---|---|
| `SAINTE_LAGUE` *(default)* | Sainte-Laguë/Schepers method, also known as the Webster method. Used by the German Bundestag. Favours neither large nor small parties. |
| `D_HONDT` | D'Hondt method (highest averages). Used in many European countries. Slightly favours larger parties. |
| `HARE_NIEMEYER` | Hare-Niemeyer method (largest remainder). First allocates seats based on the integer part of each party's quota, then awards remaining seats to the parties with the largest remainders. |

For links to further references see [`SeatDistributionMethod`](global_configuration.md) in the global configuration.

---

## Configuration Parameters

| Parameter | Class | Description |
|---|---|---|
| `seat_distribution_method` | `ElectionEvaluator` | Apportionment method (default: `SAINTE_LAGUE`) |
| `parliament_majority_margin` | `ElectionConfig` | Government margin — determines the return value of `getParliamentMajoritySeats()` |

---

## Execution in the Simulation

The class [`SeatDistributor`](../../src/ipres/seat_distributor.py) performs the seat allocation. It can be called directly or implicitly via `ElectionEvaluator.evaluate()`.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, SuperMajorityMargin, MarginUnit)
import pandas as pd

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'constituency_size': [100_000] * 5,
}))
config = ElectionConfig(
    constituencies_config=cc,
    participating_parties=['A', 'B', 'C'],
    parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
)

# A wins with 60 % > parliament threshold 55 % → Case 2: proportional distribution
election = Election(electionConfig=config)
votes = {c: {'A': 60, 'B': 25, 'C': 15} for c in ['C1', 'C2', 'C3', 'C4', 'C5']}
election.start(votes=votes)

seats = SeatDistributor().run(election)
print(seats)  # {'A': 6, 'B': 2, 'C': 2}
```
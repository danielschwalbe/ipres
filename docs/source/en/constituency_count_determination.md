# Constituency Count Determination

After seat allocation, the number of constituencies assigned to each party is determined. The core principle: half of a party's allocated seats are filled via direct constituency mandates – elected by citizens. The party fills the other half itself. This ensures democratic oversight by citizens on the one hand – voters know their representative personally – while on the other hand, parties can deliberately place subject-matter experts in Parliament who do not necessarily need to be close to the people.

**Base formula:** `constituency_count(party) = parliamentary_seats(party) // 2`

---

## The Integer Division Problem

Dividing by 2 using integer division creates a structural issue: parties with an **odd** seat count lose half a constituency right through rounding down. This means the sum of the base allocations can be smaller than the total number of constituencies:

```
sum(seats_i // 2)  <  sum(seats_i) // 2
```

**Example** (7 constituencies, 14 parliamentary seats):

| Party | Seats | Base allocation (`// 2`) |
|-------|-------|--------------------|
| A     | 10    | 5                  |
| B     | 3     | 1                  |
| C     | 1     | 0                  |
| **Σ** | 14    | **6** ← deficit 1  |

The sum of the base allocations is 6, even though 7 constituencies must be assigned. The correction awards the missing +1 to one of the parties with an odd seat count (here B or C).

---

## Correction Strategy

The missing +1 (or several, if multiple parties are affected) is awarded according to a configurable strategy. Only parties with an **odd** seat count are eligible, since only for them is a correction mathematically justified.

| Strategy | Description |
|---|---|
| `FAVOR_LARGE_PARTIES` *(default)* | The party (or parties) with the most seats receive the +1. |
| `FAVOR_SMALL_PARTIES` | The party (or parties) with the fewest seats receive the +1. |
| `PROPORTIONAL` | Random, weighted by seat count (larger parties more likely). |
| `PROPORTIONAL_REVERSED` | Random, inversely weighted (smaller parties more likely). |
| `RANDOM` | Uniform random selection among parties with odd seat counts. |
| `NEGOTIATED` | An external callback function decides which parties receive the +1. |

In the example above with `FAVOR_LARGE_PARTIES`: B has more seats than C, so B receives the +1 → B: 2, C: 0.

**Note**: The correction procedure also determines on a case-by-case basis whether a party with only one seat may fill it with a constituency representative.

---

## Effect of `constituency_representation`

This parameter (from the global configuration) controls which parties receive constituencies at all:

- **`ENTIRE_PARLIAMENT`** *(default)*: All parties receive constituencies proportional to their seats.
- **`GOVERNING_MAJORITY`**: Only the governing parties receive constituencies. The opposition receives 0 constituencies.

---

## Configuration Parameters

| Parameter | Class | Description |
|---|---|---|
| `quota_correction_strategy` | `ElectionEvaluator` | Correction strategy (default: `FAVOR_LARGE_PARTIES`) |
| `constituency_representation` | `ElectionConfig` + `ElectionEvaluator` | Which parties receive constituencies? |

---

## Execution in the Simulation

The class [`ConstituencyCountDeterminer`](../../src/ipres/constituency_count_determiner.py) performs this step. It takes the seat allocation result as input.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, ConstituencyCountDeterminer,
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
)

election = Election(electionConfig=config)
votes = {c: {'A': 60, 'B': 25, 'C': 15} for c in ['C1', 'C2', 'C3', 'C4', 'C5']}
election.start(votes=votes)

seats = SeatDistributor().run(election)               # {'A': 6, 'B': 2, 'C': 2}
counts = ConstituencyCountDeterminer().run(election, seats)
print(counts)  # {'A': 3, 'B': 1, 'C': 1}
```
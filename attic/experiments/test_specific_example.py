"""
Test the specific example without tie-breaking.
"""

import numpy as np
import pandas as pd
from itertools import permutations
from ipres.allocation import allocate_constituencies_greedy


def brute_force_optimal(importance_matrix, quotas):
    """Find optimal allocation by trying all possibilities."""
    constituencies = list(importance_matrix.index)
    parties = list(importance_matrix.columns)

    best_score = -1
    best_allocation = None

    # Generate all possible allocations
    n = len(constituencies)

    # Create list of party assignments respecting quotas
    party_list = []
    for party, quota in quotas.items():
        party_list.extend([party] * quota)

    # Try all permutations
    for perm in permutations(party_list):
        allocation = {constituencies[i]: perm[i] for i in range(n)}

        # Calculate score
        score = sum(importance_matrix.loc[const, party]
                   for const, party in allocation.items())

        if score > best_score:
            best_score = score
            best_allocation = allocation.copy()

    return best_allocation, best_score


# Your example
importance_matrix = pd.DataFrame({
    "A": [7, 5, 1, 1],
    "B": [5, 1, 5, 1],
    "C": [1, 6, 4, 5]
}, index=["WK1", "WK2", "WK3", "WK4"])

quotas = {"A": 2, "B": 1, "C": 1}

print("="*70)
print("Test: User's Example (without tie-breaking issues)")
print("="*70)
print("\nImportance Matrix:")
print(importance_matrix)
print(f"\nQuotas: {quotas}")

# Greedy
greedy_alloc = allocate_constituencies_greedy(
    importance_matrix, quotas, np.random.default_rng(42)
)
greedy_score = sum(importance_matrix.loc[const, party]
                  for const, party in greedy_alloc.items())

print(f"\n{'─'*70}")
print("GREEDY Allocation:")
print(f"{'─'*70}")
for const in sorted(greedy_alloc.keys()):
    party = greedy_alloc[const]
    score = importance_matrix.loc[const, party]
    print(f"  {const} → {party} (Wichtigkeit: {score})")

# Group by party
party_totals = {}
for const, party in greedy_alloc.items():
    if party not in party_totals:
        party_totals[party] = []
    party_totals[party].append((const, importance_matrix.loc[const, party]))

print(f"\nZusammenfassung:")
for party in sorted(party_totals.keys()):
    constituencies = party_totals[party]
    total = sum(score for _, score in constituencies)
    wk_list = ", ".join(f"{c}({s})" for c, s in constituencies)
    print(f"  {party}: {wk_list} = {total}")

print(f"\nGreedy Gesamt-Score: {greedy_score}")

# Brute force optimal
optimal_alloc, optimal_score = brute_force_optimal(importance_matrix, quotas)

print(f"\n{'─'*70}")
print("OPTIMAL Allocation:")
print(f"{'─'*70}")
for const in sorted(optimal_alloc.keys()):
    party = optimal_alloc[const]
    score = importance_matrix.loc[const, party]
    print(f"  {const} → {party} (Wichtigkeit: {score})")

# Group by party
party_totals = {}
for const, party in optimal_alloc.items():
    if party not in party_totals:
        party_totals[party] = []
    party_totals[party].append((const, importance_matrix.loc[const, party]))

print(f"\nZusammenfassung:")
for party in sorted(party_totals.keys()):
    constituencies = party_totals[party]
    total = sum(score for _, score in constituencies)
    wk_list = ", ".join(f"{c}({s})" for c, s in constituencies)
    print(f"  {party}: {wk_list} = {total}")

print(f"\nOptimal Gesamt-Score: {optimal_score}")

print(f"\n{'='*70}")
if greedy_score < optimal_score:
    gap = optimal_score - greedy_score
    print(f"⚠️  GREEDY IST SUBOPTIMAL!")
    print(f"    Gap: {gap} ({100*gap/optimal_score:.1f}% schlechter)")
else:
    print(f"✓ Greedy ist optimal für dieses Beispiel")
print(f"{'='*70}")

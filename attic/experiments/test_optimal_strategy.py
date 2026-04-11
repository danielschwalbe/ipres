"""
Test the optimal allocation strategy.
"""

import numpy as np
import pandas as pd
from ipres.allocation import (
    allocate_constituencies_greedy,
    allocate_constituencies_optimal,
    allocate_constituencies_stable
)


def test_optimal_vs_greedy():
    """Test that optimal beats greedy on the known suboptimal example."""

    # The example where greedy fails
    importance_matrix = pd.DataFrame({
        "A": [7, 5, 1, 1],
        "B": [5, 1, 5, 1],
        "C": [1, 6, 4, 5]
    }, index=["WK1", "WK2", "WK3", "WK4"])

    quotas = {"A": 2, "B": 1, "C": 1}

    print("="*70)
    print("Test: Optimal vs Greedy vs Stable Matching")
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
    party_totals = {}
    for const, party in sorted(greedy_alloc.items()):
        score = importance_matrix.loc[const, party]
        print(f"  {const} → {party} ({score})")
        if party not in party_totals:
            party_totals[party] = []
        party_totals[party].append((const, score))

    print("\nZusammenfassung:")
    for party in sorted(party_totals.keys()):
        constituencies = party_totals[party]
        total = sum(s for _, s in constituencies)
        wk_list = ", ".join(f"{c}({s})" for c, s in constituencies)
        print(f"  {party}: {wk_list} = {total}")
    print(f"\nGreedy Score: {greedy_score}")

    # Optimal
    optimal_alloc = allocate_constituencies_optimal(
        importance_matrix, quotas
    )
    optimal_score = sum(importance_matrix.loc[const, party]
                       for const, party in optimal_alloc.items())

    print(f"\n{'─'*70}")
    print("OPTIMAL Allocation:")
    print(f"{'─'*70}")
    party_totals = {}
    for const, party in sorted(optimal_alloc.items()):
        score = importance_matrix.loc[const, party]
        print(f"  {const} → {party} ({score})")
        if party not in party_totals:
            party_totals[party] = []
        party_totals[party].append((const, score))

    print("\nZusammenfassung:")
    for party in sorted(party_totals.keys()):
        constituencies = party_totals[party]
        total = sum(s for _, s in constituencies)
        wk_list = ", ".join(f"{c}({s})" for c, s in constituencies)
        print(f"  {party}: {wk_list} = {total}")
    print(f"\nOptimal Score: {optimal_score}")

    # Stable Matching
    stable_alloc = allocate_constituencies_stable(
        importance_matrix, quotas, np.random.default_rng(42)
    )
    stable_score = sum(importance_matrix.loc[const, party]
                       for const, party in stable_alloc.items())

    print(f"\n{'─'*70}")
    print("STABLE MATCHING Allocation:")
    print(f"{'─'*70}")
    party_totals = {}
    for const, party in sorted(stable_alloc.items()):
        score = importance_matrix.loc[const, party]
        print(f"  {const} → {party} ({score})")
        if party not in party_totals:
            party_totals[party] = []
        party_totals[party].append((const, score))

    print("\nZusammenfassung:")
    for party in sorted(party_totals.keys()):
        constituencies = party_totals[party]
        total = sum(s for _, s in constituencies)
        wk_list = ", ".join(f"{c}({s})" for c, s in constituencies)
        print(f"  {party}: {wk_list} = {total}")
    print(f"\nStable Matching Score: {stable_score}")

    print(f"\n{'='*70}")
    print("COMPARISON:")
    print(f"{'='*70}")
    print(f"  Greedy:          {greedy_score}")
    print(f"  Stable Matching: {stable_score}")
    print(f"  Optimal:         {optimal_score}")

    if optimal_score > max(greedy_score, stable_score):
        print(f"\n✓ Optimal is BETTER than both other strategies!")
        print(f"  vs Greedy:  +{optimal_score - greedy_score} (+{100*(optimal_score-greedy_score)/greedy_score:.1f}%)")
        print(f"  vs Stable:  +{optimal_score - stable_score} (+{100*(optimal_score-stable_score)/stable_score:.1f}%)")
    elif optimal_score == greedy_score == stable_score:
        print(f"\n✓ All strategies found the same optimal solution")
    elif optimal_score == greedy_score > stable_score:
        print(f"\n✓ Optimal and Greedy found the same solution, better than Stable")
    elif optimal_score == stable_score > greedy_score:
        print(f"\n✓ Optimal and Stable found the same solution, better than Greedy")
    else:
        print(f"\n⚠️  Unexpected result pattern")
    print(f"{'='*70}")

    # Verify optimal is truly optimal
    assert optimal_score >= greedy_score, "Optimal must be at least as good as greedy"
    assert optimal_score >= stable_score, "Optimal must be at least as good as stable matching"
    assert optimal_score == 22, "Expected optimal score is 22"


if __name__ == "__main__":
    test_optimal_vs_greedy()
    print("\n✓ All tests passed!")

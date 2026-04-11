"""
Test whether Greedy is always optimal for constituency allocation.
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
    # This is exponential - only works for small examples!
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


def test_example(importance_matrix, quotas, name):
    """Test a specific example."""
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"{'='*70}")
    print("\nImportance Matrix:")
    print(importance_matrix)
    print(f"\nQuotas: {quotas}")

    # Greedy
    greedy_alloc = allocate_constituencies_greedy(
        importance_matrix, quotas, np.random.default_rng(42)
    )
    greedy_score = sum(importance_matrix.loc[const, party]
                      for const, party in greedy_alloc.items())

    print(f"\nGreedy Allocation:")
    for const, party in sorted(greedy_alloc.items()):
        score = importance_matrix.loc[const, party]
        print(f"  {const} → {party} ({score})")
    print(f"Greedy Score: {greedy_score}")

    # Brute force optimal
    optimal_alloc, optimal_score = brute_force_optimal(importance_matrix, quotas)

    print(f"\nOptimal Allocation:")
    for const, party in sorted(optimal_alloc.items()):
        score = importance_matrix.loc[const, party]
        print(f"  {const} → {party} ({score})")
    print(f"Optimal Score: {optimal_score}")

    if greedy_score < optimal_score:
        print(f"\n⚠️  GREEDY IS SUBOPTIMAL! Gap: {optimal_score - greedy_score}")
        return False
    else:
        print(f"\n✓ Greedy is optimal for this example")
        return True


def main():
    print("Testing Greedy Optimality")
    print("="*70)

    all_optimal = True

    # Test 1: Simple 3-party example
    test1 = pd.DataFrame({
        "A": [10, 10, 0],
        "B": [9,  0,  9],
        "C": [0,  9,  9]
    }, index=["WK1", "WK2", "WK3"])
    quotas1 = {"A": 1, "B": 1, "C": 1}
    all_optimal &= test_example(test1, quotas1, "Symmetric case")

    # Test 2: Asymmetric case
    test2 = pd.DataFrame({
        "A": [100, 1,  1,  1],
        "B": [99,  98, 2,  2],
        "C": [2,   97, 96, 3]
    }, index=["WK1", "WK2", "WK3", "WK4"])
    quotas2 = {"A": 2, "B": 1, "C": 1}
    all_optimal &= test_example(test2, quotas2, "Asymmetric quotas")

    # Test 3: Blocking scenario
    test3 = pd.DataFrame({
        "A": [10, 9,  1],
        "B": [9,  1,  9],
        "C": [1,  10, 9]
    }, index=["WK1", "WK2", "WK3"])
    quotas3 = {"A": 1, "B": 1, "C": 1}
    all_optimal &= test_example(test3, quotas3, "Potential blocking")

    # Test 4: Crafted to break greedy
    test4 = pd.DataFrame({
        "A": [10, 5,  5],
        "B": [9,  9,  1],
        "C": [1,  8,  8]
    }, index=["WK1", "WK2", "WK3"])
    quotas4 = {"A": 1, "B": 1, "C": 1}
    all_optimal &= test_example(test4, quotas4, "Crafted to break greedy")

    # Test 5: Another attempt
    test5 = pd.DataFrame({
        "A": [6, 5, 1, 1],
        "B": [5, 1, 5, 1],
        "C": [1, 5, 4, 5]
    }, index=["WK1", "WK2", "WK3", "WK4"])
    quotas5 = {"A": 2, "B": 1, "C": 1}
    all_optimal &= test_example(test5, quotas5, "Complex interdependencies")

    print(f"\n\n{'='*70}")
    if all_optimal:
        print("✓ Greedy was optimal in all test cases")
    else:
        print("⚠️  Greedy was suboptimal in at least one case!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

"""
Script to find a concrete example where Greedy and Stable Matching produce different results.
"""

import numpy as np
import pandas as pd
from ipres.allocation import allocate_constituencies_greedy, allocate_constituencies_stable


def create_test_scenario(seed):
    """Create a test scenario with specific seed."""
    rng = np.random.default_rng(seed)

    # 6 constituencies, 2 parties
    n_constituencies = 6
    n_parties = 2

    # Generate random importance values
    importance_matrix = pd.DataFrame(
        rng.random((n_constituencies, n_parties)),
        index=[f"WK{i+1}" for i in range(n_constituencies)],
        columns=["Partei_A", "Partei_B"]
    )

    quotas = {"Partei_A": 3, "Partei_B": 3}

    return importance_matrix, quotas


def allocations_are_different(alloc1, alloc2):
    """Check if two allocations are different."""
    if set(alloc1.keys()) != set(alloc2.keys()):
        return True

    for constituency in alloc1:
        if alloc1[constituency] != alloc2[constituency]:
            return True

    return False


def print_allocation_details(importance_matrix, allocation, strategy_name):
    """Print detailed allocation information."""
    print(f"\n{'='*70}")
    print(f"{strategy_name} Allocation:")
    print(f"{'='*70}")

    # Group by party
    party_assignments = {}
    for constituency, party in allocation.items():
        if party not in party_assignments:
            party_assignments[party] = []
        party_assignments[party].append(constituency)

    # Calculate totals
    for party in sorted(party_assignments.keys()):
        constituencies = party_assignments[party]
        total_importance = sum(importance_matrix.loc[c, party] for c in constituencies)

        print(f"\n{party} bekommt: {', '.join(constituencies)}")
        print(f"  Details:")
        for c in constituencies:
            imp = importance_matrix.loc[c, party]
            print(f"    {c}: {imp:.4f}")
        print(f"  Summe: {total_importance:.4f}")

    # Calculate global total
    global_total = 0
    for constituency, party in allocation.items():
        global_total += importance_matrix.loc[constituency, party]

    print(f"\n{'─'*70}")
    print(f"Gesamt-Wichtigkeit (alle Parteien): {global_total:.4f}")
    print(f"{'─'*70}")


def check_blocking_pairs(importance_matrix, allocation, quotas):
    """Check if there are any blocking pairs in the allocation."""
    blocking_pairs = []

    # Get current assignments per party
    party_assignments = {}
    for constituency, party in allocation.items():
        if party not in party_assignments:
            party_assignments[party] = []
        party_assignments[party].append(constituency)

    # Check all possible (constituency, party) pairs
    for constituency in importance_matrix.index:
        current_party = allocation[constituency]

        for other_party in importance_matrix.columns:
            if other_party == current_party:
                continue

            # Would constituency prefer other_party over current_party?
            current_importance = importance_matrix.loc[constituency, current_party]
            other_importance = importance_matrix.loc[constituency, other_party]

            if other_importance <= current_importance:
                # Constituency doesn't prefer other party
                continue

            # Would other_party prefer this constituency over one of its current assignments?
            other_party_constituencies = party_assignments[other_party]

            # Find worst constituency currently assigned to other_party
            worst_constituency = None
            worst_importance = float('inf')

            for c in other_party_constituencies:
                imp = importance_matrix.loc[c, other_party]
                if imp < worst_importance:
                    worst_importance = imp
                    worst_constituency = c

            # If this constituency is better than worst current, it's a blocking pair
            if other_importance > worst_importance:
                blocking_pairs.append({
                    'constituency': constituency,
                    'current_party': current_party,
                    'current_importance': current_importance,
                    'blocking_party': other_party,
                    'blocking_importance': other_importance,
                    'would_replace': worst_constituency,
                    'replaced_importance': worst_importance
                })

    return blocking_pairs


def main():
    print("Suche nach einem Beispiel, wo Greedy und Stable Matching unterschiedlich sind...")
    print()

    # Try different seeds until we find a difference
    for seed in range(1000):
        importance_matrix, quotas = create_test_scenario(seed)

        # Run both strategies
        rng = np.random.default_rng(42)  # Use same RNG for both
        greedy_alloc = allocate_constituencies_greedy(
            importance_matrix, quotas, np.random.default_rng(42)
        )
        stable_alloc = allocate_constituencies_stable(
            importance_matrix, quotas, np.random.default_rng(42)
        )

        if allocations_are_different(greedy_alloc, stable_alloc):
            print(f"✓ Unterschied gefunden mit Seed {seed}!\n")

            # Print importance matrix
            print("="*70)
            print("Importance Matrix:")
            print("="*70)
            print(importance_matrix.round(4))
            print()
            print(f"Quotas: {quotas}")

            # Print Greedy allocation
            print_allocation_details(importance_matrix, greedy_alloc, "GREEDY")

            # Check for blocking pairs in Greedy
            blocking_pairs = check_blocking_pairs(importance_matrix, greedy_alloc, quotas)
            if blocking_pairs:
                print("\n⚠️  BLOCKING PAIRS in Greedy Allocation:")
                for bp in blocking_pairs:
                    print(f"\n  • {bp['constituency']} + {bp['blocking_party']} bilden ein blocking pair:")
                    print(f"    - {bp['constituency']} ist aktuell bei {bp['current_party']} (Wichtigkeit: {bp['current_importance']:.4f})")
                    print(f"    - {bp['blocking_party']} würde {bp['constituency']} bevorzugen (Wichtigkeit: {bp['blocking_importance']:.4f})")
                    print(f"    - {bp['blocking_party']} würde dafür {bp['would_replace']} aufgeben (Wichtigkeit: {bp['replaced_importance']:.4f})")
                    print(f"    - Beide würden den Tausch bevorzugen!")

            # Print Stable Matching allocation
            print_allocation_details(importance_matrix, stable_alloc, "STABLE MATCHING")

            # Check for blocking pairs in Stable Matching
            blocking_pairs = check_blocking_pairs(importance_matrix, stable_alloc, quotas)
            if blocking_pairs:
                print("\n⚠️  BLOCKING PAIRS in Stable Matching (sollte nicht passieren!):")
                for bp in blocking_pairs:
                    print(f"  • {bp['constituency']} + {bp['blocking_party']}")
            else:
                print("\n✓ Keine blocking pairs in Stable Matching - Allocation ist stabil!")

            # Show the key differences
            print("\n" + "="*70)
            print("UNTERSCHIEDE:")
            print("="*70)
            for constituency in importance_matrix.index:
                if greedy_alloc[constituency] != stable_alloc[constituency]:
                    greedy_party = greedy_alloc[constituency]
                    stable_party = stable_alloc[constituency]
                    greedy_imp = importance_matrix.loc[constituency, greedy_party]
                    stable_imp = importance_matrix.loc[constituency, stable_party]

                    print(f"\n{constituency}:")
                    print(f"  Greedy:  → {greedy_party} (Wichtigkeit: {greedy_imp:.4f})")
                    print(f"  Stable:  → {stable_party} (Wichtigkeit: {stable_imp:.4f})")

            break
    else:
        print("Kein Unterschied in 1000 Versuchen gefunden.")


if __name__ == "__main__":
    main()

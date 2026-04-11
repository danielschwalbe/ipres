"""
Test demonstrating the problem where a party with votes in only ONE constituency
but quota > 1 gets assigned to OTHER constituencies where it has 0 votes.

This test creates a minimal example with injected test data to show this structural issue.
"""

import numpy as np
import pandas as pd
import pytest

from ipres.allocation import allocate_constituencies_optimal
from ipres.vote_matrix import VoteMatrix
from ipres.vote_matrix_analyzer import VoteMatrixAnalyzer
from ipres.constituencies_config import ConstituenciesConfig
from ipres.contestant import Contestant


def test_party_with_single_constituency_votes_gets_other_constituencies():
    """
    Test case demonstrating the quota > 1 problem.

    Scenario:
    - 6 constituencies (C1-C6)
    - 3 parties: A, B, C
    - Party C has votes ONLY in constituency C1 (nowhere else)
    - But Party C gets enough total votes to receive 2 seats → quota = 1
    - Expected problem: Party C might get assigned to C2 where it has 0 votes

    This happens because:
    1. The quota system requires sum(quotas) = number_of_constituencies
    2. If Party C has quota > number_of_constituencies_with_votes, it MUST
       get assigned to constituencies where it has 0 votes
    """

    # Setup: 6 constituencies
    constituency_config = ConstituenciesConfig.from_random(
        M=6,
        Smin=1000,
        Smax=1000
    )

    # Create contestants
    contestants = [
        Contestant.from_party("Party_A"),
        Contestant.from_party("Party_B"),
        Contestant.from_party("Party_C"),
    ]

    # Create vote matrix manually:
    # Party_C has ALL its votes (500) in C1 only
    # Party_A and Party_B are distributed across all constituencies
    vote_matrix = pd.DataFrame({
        "Party_A": [300, 400, 350, 380, 420, 390],  # Well distributed
        "Party_B": [200, 300, 250, 220, 280, 260],  # Well distributed
        "Party_C": [500,   0,   0,   0,   0,   0],  # ONLY in C1!
    }, index=[f"Constituency_{i}" for i in range(1, 7)])

    # Create vote matrix with injected votes
    vm = VoteMatrix.generate(
        constituencies_config=constituency_config,
        contestants=contestants,
        vote_matrix=vote_matrix
    )

    # Calculate importance matrix
    ballotEvaluator = VoteMatrixAnalyzer(vm.getVotes())
    importance_matrix = ballotEvaluator.getConstituencyImportanceMatrix()

    # Print for debugging
    print("\n=== Vote Matrix ===")
    print(vote_matrix)
    print(f"\nTotal votes: {vote_matrix.sum().sum()}")
    print(f"Party_A: {vote_matrix['Party_A'].sum()} votes")
    print(f"Party_B: {vote_matrix['Party_B'].sum()} votes")
    print(f"Party_C: {vote_matrix['Party_C'].sum()} votes (ALL in C1!)")

    print("\n=== Importance Matrix ===")
    print(importance_matrix)

    # Simulate seat distribution
    # Total votes = 2240 + 1510 + 500 = 4250
    # Party_A: 2240/4250 ≈ 52.7% → ~3 seats → quota = 1 or 2
    # Party_B: 1510/4250 ≈ 35.5% → ~2 seats → quota = 1
    # Party_C:  500/4250 ≈ 11.8% → ~1 seat  → quota = 0 or 1

    # But let's force the problem: give Party_C quota = 2
    # This simulates a scenario where Party_C gets enough seats but only has votes in one place
    quotas = {
        "Party_A": 2,
        "Party_B": 2,
        "Party_C": 2,  # ← PROBLEM: Party_C only has votes in 1 constituency!
    }

    # Allocate constituencies
    rng = np.random.default_rng(42)
    allocation = allocate_constituencies_optimal(importance_matrix, quotas, rng)

    print("\n=== Constituency Allocation ===")
    for constituency, party in sorted(allocation.items()):
        votes = vote_matrix.loc[constituency, party]
        print(f"{constituency} → {party} (votes: {votes})")

    # Analyze Party_C's assignments
    party_c_constituencies = [c for c, p in allocation.items() if p == "Party_C"]
    print(f"\n=== Party_C Analysis ===")
    print(f"Party_C assigned to: {party_c_constituencies}")
    print(f"Party_C quota: {quotas['Party_C']}")

    # Check if Party_C got assigned to constituencies where it has 0 votes
    party_c_assignments_with_zero_votes = []
    for constituency in party_c_constituencies:
        votes = vote_matrix.loc[constituency, "Party_C"]
        print(f"  {constituency}: {votes} votes")
        if votes == 0:
            party_c_assignments_with_zero_votes.append(constituency)

    # THE PROBLEM: Party_C gets assigned to constituencies where it has 0 votes!
    print(f"\nParty_C constituencies with 0 votes: {party_c_assignments_with_zero_votes}")

    # Assertions documenting the problem
    assert len(party_c_constituencies) == 2, "Party_C should get 2 constituencies (quota=2)"
    assert "Constituency_1" in party_c_constituencies, \
        "Party_C should get C1 (where it has all its votes)"

    # This assertion FAILS if the problem exists:
    # Party_C should ONLY be assigned to constituencies where it has votes
    has_zero_vote_assignments = len(party_c_assignments_with_zero_votes) > 0

    if has_zero_vote_assignments:
        print("\n⚠️  PROBLEM CONFIRMED: Party_C is assigned to constituencies with 0 votes!")
        print(f"    This is structurally unavoidable when quota > constituencies_with_votes")

    # We document the problem but don't fail the test (since this is the current behavior)
    # In a real scenario, this would need to be fixed at the quota calculation level
    assert has_zero_vote_assignments, \
        "Expected: Party_C gets constituencies where it has 0 votes (documenting the problem)"


def test_party_with_single_constituency_high_importance():
    """
    Test that the improved importance calculation gives maximum priority to
    parties that only have votes in one constituency.

    This test verifies that the importance matrix correctly prioritizes such cases.
    """

    # Setup: 4 constituencies
    constituency_config = ConstituenciesConfig.from_random(
        M=4,
        Smin=1000,
        Smax=1000
    )

    contestants = [
        Contestant.from_party("Party_A"),
        Contestant.from_party("Party_B"),
        Contestant.from_party("Party_C"),
    ]

    # Party_A has votes only in Constituency_1
    # Party_B has votes only in Constituency_1 (competing with A)
    # Party_C is well distributed
    vote_matrix = pd.DataFrame({
        "Party_A": [1000,    0,   0,   0],  # Only in Constituency_1
        "Party_B": [ 800,    0,   0,   0],  # Only in Constituency_1 (less than A)
        "Party_C": [ 200, 600, 600, 600],  # Well distributed
    }, index=[f"Constituency_{i}" for i in range(1, 5)])

    vm = VoteMatrix.generate(
        constituencies_config=constituency_config,
        contestants=contestants,
        vote_matrix=vote_matrix
    )

    ballotEvaluator = VoteMatrixAnalyzer(vm.getVotes())

    importance_matrix = ballotEvaluator.getConstituencyImportanceMatrix()

    print("\n=== Vote Matrix ===")
    print(vote_matrix)

    print("\n=== Importance Matrix ===")
    print(importance_matrix)

    # Check importance values for Constituency_1
    importance_a_c1 = importance_matrix.loc["Constituency_1", "Party_A"]
    importance_b_c1 = importance_matrix.loc["Constituency_1", "Party_B"]
    importance_c_c1 = importance_matrix.loc["Constituency_1", "Party_C"]

    print(f"\nImportance of Constituency_1 for Party_A (denominator=0): {importance_a_c1:.2f}")
    print(f"\nImportance of Constituency_1 for Party_B (denominator=0): {importance_b_c1:.2f}")
    print(f"Importance of Constituency_1 for Party_C (normal case):   {importance_c_c1:.2f}")

    # Verify that denominator=0 cases get higher importance than normal cases
    total_votes = vote_matrix.sum().sum()
    print(f"\nTotal votes in system: {total_votes}")

    # Both Party_A and Party_B should have importance > total_votes
    assert importance_a_c1 > total_votes, \
        "Party_A (denominator=0) should have importance > total_votes"
    assert importance_b_c1 > total_votes, \
        "Party_B (denominator=0) should have importance > total_votes"

    # Party_A should beat Party_B (more votes in C1)
    assert importance_a_c1 > importance_b_c1, \
        "Party_A should have higher importance than Party_B (more votes)"

    # Both should beat Party_C
    assert importance_a_c1 > importance_c_c1
    assert importance_b_c1 > importance_c_c1

    print("\n✓ Importance calculation correctly prioritizes parties with denominator=0")

    # Now compute the allocation to see what happens
    # Total votes = 1000 + 800 + 2000 = 3800
    # Party_A: 1000/3800 ≈ 26.3% → 1 seat (at 4 total constituencies, each party gets quotas)
    # Party_B: 800/3800 ≈ 21.1% → 1 seat
    # Party_C: 2000/3800 ≈ 52.6% → 2 seats
    # Quotas would be: A=0, B=0, C=2 OR A=1, B=1, C=2 depending on rounding

    # Let's force quotas to show the allocation behavior
    quotas = {
        "Party_A": 1,  # Has votes only in Constituency_1
        "Party_B": 1,  # Has votes only in Constituency_1 (competes with A)
        "Party_C": 2,  # Well distributed
    }

    print("\n=== Allocation Test ===")
    print(f"Quotas: {quotas}")

    rng = np.random.default_rng(42)
    allocation = allocate_constituencies_optimal(importance_matrix, quotas, rng)

    print("\n=== Constituency Allocation ===")
    for constituency in sorted(allocation.keys()):
        party = allocation[constituency]
        votes = vote_matrix.loc[constituency, party]
        print(f"{constituency} → {party} (votes: {votes})")

    # Verify that Party_A gets Constituency_1 (where it has all its votes)
    # Party_A should win over Party_B because it has more votes (1000 vs 800)
    assert allocation["Constituency_1"] == "Party_A", \
        "Party_A should get Constituency_1 (highest importance due to more votes)"

    print("\n✓ Party_A correctly assigned to Constituency_1 (beats Party_B with higher vote count)")



if __name__ == "__main__":
    # Run tests
    test_party_with_single_constituency_high_importance()
    print("\n" + "="*70 + "\n")
    test_party_with_single_constituency_votes_gets_other_constituencies()

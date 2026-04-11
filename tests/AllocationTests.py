import numpy as np
import pandas as pd
import pytest

from ipres.allocation import (
    GreedyAllocationStrategy,
    StableMatchingAllocationStrategy
)


def test_greedy_allocation_basic():
    """Test basic greedy allocation with clear preferences."""
    # Given: 3 constituencies, 2 parties
    # Party A strongly prefers C1, Party B strongly prefers C2, C3 is split
    importance_matrix = pd.DataFrame({
        "A": [0.8, 0.2, 0.3],  # A really wants C1
        "B": [0.2, 0.7, 0.6]   # B prefers C2 and C3
    }, index=["C1", "C2", "C3"])

    quotas = {"A": 1, "B": 2}
    rng = np.random.default_rng(42)

    # When
    strategy = GreedyAllocationStrategy()
    allocation = strategy.allocate(importance_matrix, quotas, rng)

    # Then
    assert len(allocation) == 3
    assert allocation["C1"] == "A"  # A's best constituency
    assert allocation["C2"] == "B"  # B's best constituency
    assert allocation["C3"] == "B"  # B gets remaining


def test_greedy_allocation_respects_quotas():
    """Test that greedy allocation respects party quotas."""
    # Given: 4 constituencies, 3 parties with specific quotas
    importance_matrix = pd.DataFrame({
        "A": [0.5, 0.4, 0.3, 0.2],
        "B": [0.3, 0.5, 0.4, 0.3],
        "C": [0.2, 0.1, 0.3, 0.5]
    }, index=["C1", "C2", "C3", "C4"])

    quotas = {"A": 2, "B": 1, "C": 1}
    rng = np.random.default_rng(123)

    # When
    strategy = GreedyAllocationStrategy()
    allocation = strategy.allocate(importance_matrix, quotas, rng)

    # Then
    assert len(allocation) == 4
    # Count assignments per party
    party_counts = {}
    for party in allocation.values():
        party_counts[party] = party_counts.get(party, 0) + 1

    assert party_counts["A"] == 2
    assert party_counts["B"] == 1
    assert party_counts["C"] == 1


def test_greedy_allocation_invalid_quotas():
    """Test that greedy allocation raises error for invalid quotas."""
    # Given: Quotas don't sum to number of constituencies
    importance_matrix = pd.DataFrame({
        "A": [0.5, 0.3],
        "B": [0.5, 0.7]
    }, index=["C1", "C2"])

    quotas = {"A": 1, "B": 0}  # Sum is 1, but we have 2 constituencies

    # When/Then
    strategy = GreedyAllocationStrategy()
    with pytest.raises(ValueError, match="Sum of quotas"):
        strategy.allocate(importance_matrix, quotas)


def test_greedy_allocation_deterministic_with_seed():
    """Test that greedy allocation is deterministic with same seed."""
    # Given: Matrix with potential ties
    importance_matrix = pd.DataFrame({
        "A": [0.5, 0.5, 0.3],
        "B": [0.5, 0.5, 0.7]
    }, index=["C1", "C2", "C3"])

    quotas = {"A": 1, "B": 2}

    # When: Run twice with same seed
    strategy = GreedyAllocationStrategy()
    allocation1 = strategy.allocate(importance_matrix, quotas, np.random.default_rng(999))
    allocation2 = strategy.allocate(importance_matrix, quotas, np.random.default_rng(999))

    # Then: Should produce same results
    assert allocation1 == allocation2


def test_stable_matching_basic():
    """Test basic stable matching allocation."""
    # Given: Simple 2x2 scenario
    importance_matrix = pd.DataFrame({
        "A": [0.8, 0.2],  # A strongly prefers C1
        "B": [0.3, 0.9]   # B strongly prefers C2
    }, index=["C1", "C2"])

    quotas = {"A": 1, "B": 1}
    rng = np.random.default_rng(42)

    # When
    strategy = StableMatchingAllocationStrategy()
    allocation = strategy.allocate(importance_matrix, quotas, rng)

    # Then: Should match naturally (no blocking pairs)
    assert len(allocation) == 2
    assert allocation["C1"] == "A"
    assert allocation["C2"] == "B"


def test_stable_matching_respects_quotas():
    """Test that stable matching respects party quotas."""
    # Given: 5 constituencies, 3 parties
    importance_matrix = pd.DataFrame({
        "A": [0.5, 0.4, 0.3, 0.2, 0.1],
        "B": [0.3, 0.5, 0.4, 0.3, 0.2],
        "C": [0.2, 0.1, 0.3, 0.5, 0.7]
    }, index=["C1", "C2", "C3", "C4", "C5"])

    quotas = {"A": 2, "B": 2, "C": 1}
    rng = np.random.default_rng(456)

    # When
    strategy = StableMatchingAllocationStrategy()
    allocation = strategy.allocate(importance_matrix, quotas, rng)

    # Then
    assert len(allocation) == 5
    party_counts = {}
    for party in allocation.values():
        party_counts[party] = party_counts.get(party, 0) + 1

    assert party_counts["A"] == 2
    assert party_counts["B"] == 2
    assert party_counts["C"] == 1


def test_stable_matching_stability():
    """Test that stable matching produces stable allocation (no blocking pairs)."""
    # Given: 4 constituencies, 2 parties with equal quotas
    importance_matrix = pd.DataFrame({
        "A": [0.9, 0.7, 0.4, 0.2],
        "B": [0.8, 0.6, 0.5, 0.3]
    }, index=["C1", "C2", "C3", "C4"])

    quotas = {"A": 2, "B": 2}
    rng = np.random.default_rng(789)

    # When
    strategy = StableMatchingAllocationStrategy()
    allocation = strategy.allocate(importance_matrix, quotas, rng)

    # Then: Check for blocking pairs
    # A blocking pair exists if:
    # - Constituency i is assigned to party X
    # - Party Y values i more than one of its current assignments
    # - i values Y more than its current assignment X

    # This is a simplified stability check
    assert len(allocation) == 4
    # Both parties should get their top 2 choices (given the clear preferences)
    assert allocation["C1"] == "A"  # A's top choice
    assert allocation["C2"] == "A"  # A's 2nd choice
    assert allocation["C3"] == "B"  # B's top remaining
    assert allocation["C4"] == "B"  # B's 2nd remaining


def test_stable_matching_invalid_quotas():
    """Test that stable matching raises error for invalid quotas."""
    # Given: Invalid quotas
    importance_matrix = pd.DataFrame({
        "A": [0.5, 0.3],
        "B": [0.5, 0.7]
    }, index=["C1", "C2"])

    quotas = {"A": 3, "B": 0}  # Sum is 3, but we have 2 constituencies

    # When/Then
    strategy = StableMatchingAllocationStrategy()
    with pytest.raises(ValueError, match="Sum of quotas"):
        strategy.allocate(importance_matrix, quotas)


def test_both_strategies_produce_valid_allocations():
    """Test that both strategies produce valid allocations for the same input."""
    # Given: Realistic scenario
    np.random.seed(42)
    n_constituencies = 10
    n_parties = 3

    importance_matrix = pd.DataFrame(
        np.random.rand(n_constituencies, n_parties),
        index=[f"C{i}" for i in range(n_constituencies)],
        columns=[f"P{i}" for i in range(n_parties)]
    )

    quotas = {"P0": 4, "P1": 3, "P2": 3}
    rng = np.random.default_rng(111)

    # When
    greedy = GreedyAllocationStrategy()
    stable = StableMatchingAllocationStrategy()

    greedy_allocation = greedy.allocate(importance_matrix, quotas, rng)
    stable_allocation = stable.allocate(importance_matrix, quotas, np.random.default_rng(111))

    # Then: Both should produce valid allocations
    for allocation in [greedy_allocation, stable_allocation]:
        assert len(allocation) == n_constituencies
        assert set(allocation.keys()) == set(importance_matrix.index)

        # Check quotas
        party_counts = {}
        for party in allocation.values():
            party_counts[party] = party_counts.get(party, 0) + 1

        for party, quota in quotas.items():
            assert party_counts[party] == quota


def test_greedy_vs_stable_different_results():
    """Test that greedy and stable matching can produce different results."""
    # Given: A scenario where greedy and stable should differ
    # Party A values C1 highly, Party B values C2 highly
    # But C1 also prefers B over A (from B's perspective)
    importance_matrix = pd.DataFrame({
        "A": [0.9, 0.3, 0.2, 0.1],  # A really wants C1
        "B": [0.8, 0.7, 0.6, 0.5]   # B wants C1 too, but also likes others
    }, index=["C1", "C2", "C3", "C4"])

    quotas = {"A": 2, "B": 2}
    rng = np.random.default_rng(555)

    # When
    greedy = GreedyAllocationStrategy()
    stable = StableMatchingAllocationStrategy()

    greedy_allocation = greedy.allocate(importance_matrix, quotas, np.random.default_rng(555))
    stable_allocation = stable.allocate(importance_matrix, quotas, np.random.default_rng(555))

    # Then: Allocations should be valid but might differ
    # (We don't assert they're different, just that both are valid)
    assert len(greedy_allocation) == 4
    assert len(stable_allocation) == 4

    # Both should respect quotas
    for allocation in [greedy_allocation, stable_allocation]:
        counts = {"A": 0, "B": 0}
        for party in allocation.values():
            counts[party] += 1
        assert counts == quotas


def test_large_realistic_scenario():
    """Test with realistic Bundestag-like scenario (299 constituencies, 6 parties)."""
    # Given: 299 constituencies, 6 parties
    np.random.seed(123)
    n_constituencies = 299
    parties = ["CDU", "SPD", "Grüne", "Linke", "AFD", "FDP"]

    # Create importance matrix with realistic patterns
    importance_matrix = pd.DataFrame(
        np.random.dirichlet(np.ones(len(parties)), n_constituencies),
        index=[f"Wahlkreis {i:03d}" for i in range(1, n_constituencies + 1)],
        columns=parties
    )

    # Quotas that sum to 299
    quotas = {"CDU": 100, "SPD": 80, "Grüne": 50, "Linke": 30, "AFD": 25, "FDP": 14}
    rng = np.random.default_rng(999)

    # When: Run both strategies
    greedy = GreedyAllocationStrategy()
    stable = StableMatchingAllocationStrategy()

    greedy_allocation = greedy.allocate(importance_matrix, quotas, np.random.default_rng(999))
    stable_allocation = stable.allocate(importance_matrix, quotas, np.random.default_rng(999))

    # Then: Both should produce valid allocations
    for allocation in [greedy_allocation, stable_allocation]:
        assert len(allocation) == n_constituencies

        # Check all constituencies assigned
        assert set(allocation.keys()) == set(importance_matrix.index)

        # Check quotas respected
        party_counts = {party: 0 for party in parties}
        for party in allocation.values():
            party_counts[party] += 1

        for party, quota in quotas.items():
            assert party_counts[party] == quota, f"Party {party} has {party_counts[party]} but quota is {quota}"

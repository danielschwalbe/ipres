"""
Tests to verify the quota invariant in GOVERNING_MAJORITY mode.

In GOVERNING_MAJORITY mode, the fundamental invariant is:
    sum(quotas) = number_of_constituencies

where:
    quotas = getParliamentMajoritySeats() // 2

This ensures that constituency allocation always works correctly.
"""

import pytest
import pandas as pd

from ipres.election_config import ElectionConfig, ConstituencyRepresentation
from ipres.constituencies_config import ConstituenciesConfig
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def create_test_constituencies(count: int) -> ConstituenciesConfig:
    """Helper to create test constituencies configuration."""
    constituencies_df = pd.DataFrame({
        'constituency_number': range(1, count + 1),
        'constituency_name': [f'WK{i}' for i in range(1, count + 1)],
        'constituency_size': [100000] * count
    })
    return ConstituenciesConfig(constituencies_df)


@pytest.mark.parametrize("constituencies,margin_percent", [
    (1, 1.0),
    (1, 5.0),
    (10, 2.5),
    (10, 10.0),
    (50, 5.0),
    (50, 15.0),
    (100, 5.0),
    (100, 7.5),
    (100, 10.0),
    (299, 2.5),
    (299, 5.0),
    (299, 10.0),
    (500, 5.0),
    (1000, 5.0),
])
def test_quota_invariant_percent_margin(constituencies, margin_percent):
    """Test quota invariant with various constituency counts and percent margins."""
    margin = SuperMajorityMargin(margin_percent, MarginUnit.PERCENT)
    constituencies_config = create_test_constituencies(constituencies)

    config = ElectionConfig(
        constituencies_config=constituencies_config,
        participating_parties=['A', 'B'],
        parliament_majority_margin=margin,
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
    )

    # Check invariant
    gov_seats = config.getParliamentMajoritySeats()
    quotas_sum = gov_seats // 2
    expected = constituencies

    assert quotas_sum == expected, (
        f"Quota invariant violated: {constituencies} constituencies, {margin_percent}% margin\n"
        f"  Government seats: {gov_seats}\n"
        f"  Quotas sum: {quotas_sum}\n"
        f"  Expected: {expected}"
    )


@pytest.mark.parametrize("constituencies,margin_seats", [
    (50, 1),
    (50, 5),
    (50, 10),
    (100, 5),
    (100, 10),
    (100, 20),
    (299, 15),
    (299, 50),
    (500, 50),
    (500, 100),
    (1000, 100),
])
def test_quota_invariant_seats_margin(constituencies, margin_seats):
    """Test quota invariant with various constituency counts and seats margins."""
    # Only test if margin is less than half of constituencies
    if margin_seats >= constituencies // 2:
        pytest.skip(f"Margin {margin_seats} too large for {constituencies} constituencies")

    margin = SuperMajorityMargin(margin_seats, MarginUnit.SEATS)
    constituencies_config = create_test_constituencies(constituencies)

    config = ElectionConfig(
        constituencies_config=constituencies_config,
        participating_parties=['A', 'B'],
        parliament_majority_margin=margin,
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
    )

    # Check invariant
    gov_seats = config.getParliamentMajoritySeats()
    quotas_sum = gov_seats // 2
    expected = constituencies

    assert quotas_sum == expected, (
        f"Quota invariant violated: {constituencies} constituencies, {margin_seats} seats margin\n"
        f"  Government seats: {gov_seats}\n"
        f"  Quotas sum: {quotas_sum}\n"
        f"  Expected: {expected}"
    )


def test_quota_invariant_edge_case_single_constituency():
    """Test edge case with just 1 constituency."""
    margin = SuperMajorityMargin(1.0, MarginUnit.PERCENT)
    constituencies_config = create_test_constituencies(1)

    config = ElectionConfig(
        constituencies_config=constituencies_config,
        participating_parties=['A', 'B'],
        parliament_majority_margin=margin,
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
    )

    gov_seats = config.getParliamentMajoritySeats()
    quotas_sum = gov_seats // 2

    assert quotas_sum == 1, (
        f"Single constituency case failed\n"
        f"  Government seats: {gov_seats}\n"
        f"  Quotas sum: {quotas_sum}"
    )


def test_quota_invariant_floating_point_problematic_cases():
    """Test specific cases known to trigger floating-point issues."""
    # These are cases that were found to have floating-point rounding issues
    # (see analyze_rare_case.py for details)
    problematic_cases = [
        (147, 28.4),
        (162, 36.4),
        (294, 28.4),
        (309, 32.4),
        (324, 36.4),
    ]

    for constituencies, margin_percent in problematic_cases:
        margin = SuperMajorityMargin(margin_percent, MarginUnit.PERCENT)
        constituencies_config = create_test_constituencies(constituencies)

        config = ElectionConfig(
            constituencies_config=constituencies_config,
            participating_parties=['A', 'B'],
            parliament_majority_margin=margin,
            constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
        )

        gov_seats = config.getParliamentMajoritySeats()
        quotas_sum = gov_seats // 2
        expected = constituencies

        assert quotas_sum == expected, (
            f"Floating-point problematic case failed: {constituencies} constituencies, {margin_percent}% margin\n"
            f"  Government seats: {gov_seats}\n"
            f"  Quotas sum: {quotas_sum}\n"
            f"  Expected: {expected}"
        )


def test_government_majority_seats_equals_two_times_constituencies():
    """Test that getParliamentMajoritySeats() = 2 * constituencies (fundamental property)."""
    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (100, SuperMajorityMargin(7.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(5, MarginUnit.SEATS)),
        (51, SuperMajorityMargin(5, MarginUnit.SEATS)),
        (51, SuperMajorityMargin(6, MarginUnit.SEATS)),
        (52, SuperMajorityMargin(6, MarginUnit.SEATS)),
    ]

    for constituencies, margin in test_cases:
        constituencies_config = create_test_constituencies(constituencies)

        config = ElectionConfig(
            constituencies_config=constituencies_config,
            participating_parties=['A', 'B', 'C', 'D'],
            parliament_majority_margin=margin,
            constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
        )

        gov_seats = config.getParliamentMajoritySeats()
        expected = 2 * constituencies

        assert gov_seats == expected, (
            f"Government majority seats != 2 * constituencies\n"
            f"  Constituencies: {constituencies}\n"
            f"  Margin: {margin.value} {margin.unit.name}\n"
            f"  Government seats: {gov_seats}\n"
            f"  Expected: {expected}"
        )


def test_quota_correction_favor_large_parties():
    """Test FAVOR_LARGE_PARTIES strategy: largest parties get +1 first."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy

    # Total=14, Required=7, Base quotas: 4+2+0=6, Deficit=1
    # Only Large (9 seats) should get +1
    seats = {
        'Large': 9,   # Gets +1 (9//2 = 4 -> 5)
        'Medium': 5,  # No correction (5//2 = 2 -> 2)
        'Small': 0,   # No correction (0//2 = 0 -> 0)
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES,
        callback=None,
        rng=None,
        seed=None
    )

    # Only Large should get +1
    assert quotas['Large'] == 5  # 9//2 + 1
    assert quotas['Medium'] == 2  # 5//2 + 0
    assert quotas['Small'] == 0  # 0//2 + 0
    assert sum(quotas.values()) == 14 // 2  # 7


def test_quota_correction_favor_small_parties():
    """Test FAVOR_SMALL_PARTIES strategy: smallest parties get +1 first."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy

    # Total=14, Required=7, Base quotas: 4+2+0=6, Deficit=1
    # Only Small (1 seat) should get +1
    seats = {
        'Large': 9,   # No correction (9//2 = 4 -> 4)
        'Medium': 4,  # No correction (4//2 = 2 -> 2)
        'Small': 1,   # Gets +1 (1//2 = 0 -> 1)
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.FAVOR_SMALL_PARTIES,
        callback=None,
        rng=None,
        seed=None
    )

    # Only Small should get +1
    assert quotas['Large'] == 4  # 9//2 + 0
    assert quotas['Medium'] == 2  # 4//2 + 0
    assert quotas['Small'] == 1  # 1//2 + 1
    assert sum(quotas.values()) == 14 // 2  # 7


def test_quota_correction_random():
    """Test RANDOM strategy: uniform random selection."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy
    import numpy as np

    seats = {
        'A': 5,
        'B': 5,
        'C': 5,
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.RANDOM,
        callback=None,
        rng=np.random.default_rng(42),
        seed=42
    )

    # Exactly one party should get +1, sum should be correct
    assert sum(quotas.values()) == 15 // 2  # 7
    corrections = [v - 2 for v in quotas.values()]  # Base is 2 for each
    assert corrections.count(1) == 1  # Exactly one +1
    assert corrections.count(0) == 2  # Two parties without correction


def test_quota_correction_proportional():
    """Test PROPORTIONAL strategy: weighted by seat count."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy
    import numpy as np

    seats = {
        'A': 5,
        'B': 77,
        'C': 513
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.PROPORTIONAL,
        callback=None,
        rng=np.random.default_rng(42),
        seed=42
    )

    # Sum should be correct
    assert sum(quotas.values()) == 595 // 2  # 7
    assert quotas['A'] == 5 // 2 + 0
    assert quotas['B'] == 77 // 2 + 0
    assert quotas['C'] == 513 // 2 + 1


def test_quota_correction_proportional_reversed():
    """Test PROPORTIONAL_REVERSED strategy: weighted by reversed proportions."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy
    import numpy as np

    seats = {
        'A': 5,
        'B': 77,
        'C': 513,
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.PROPORTIONAL_REVERSED,
        callback=None,
        rng=np.random.default_rng(42),
        seed=42
    )

    # Sum should be correct
    assert sum(quotas.values()) == 595 // 2  # 7
    assert quotas['A'] == 5 // 2 + 1
    assert quotas['B'] == 77 // 2 + 0
    assert quotas['C'] == 513 // 2 + 0

def test_quota_correction_negotiated():
    """Test NEGOTIATED strategy: callback determines which parties get +1."""
    from ipres.party_quotas_correction import correct_party_quotas
    from ipres import QuotaCorrectionStrategy

    def my_callback(odd_seat_parties, deficit):
        # Always choose parties alphabetically
        return sorted(odd_seat_parties.keys())[:deficit]

    seats = {
        'C': 5,
        'A': 5,
        'B': 5,
    }
    base_quotas = {party: seat_count // 2 for party, seat_count in seats.items()}

    quotas = correct_party_quotas(
        quotas=base_quotas,
        seats=seats,
        strategy=QuotaCorrectionStrategy.NEGOTIATED,
        callback=my_callback,
        rng=None,
        seed=None
    )

    # A should get +1 (alphabetically first)
    assert quotas['A'] == 3  # 5//2 + 1
    assert quotas['B'] == 2  # 5//2 + 0
    assert quotas['C'] == 2  # 5//2 + 0
    assert sum(quotas.values()) == 15 // 2  # 7


def test_party_quotas_sum_insufficient_for_constituencies():
    """
    Test that quota correction ensures sum(quotas) == number_of_constituencies

    Previously, sum(a_i // 2) < sum(a_i) // 2 caused a deficit.
    Now with quota correction, this should be fixed.

    Example: a1=5, a2=5, a3=5
    - Old: sum(a_i // 2) = 5//2 + 5//2 + 5//2 = 2 + 2 + 2 = 6
    - Required: sum(a_i) // 2 = (5+5+5) // 2 = 15 // 2 = 7
    - New: quota correction adds +1 to one party, giving 3+2+2 = 7
    """
    from unittest.mock import MagicMock
    from ipres import Election, SeatDistributionMethod, QuotaCorrectionStrategy, ConstituencyCountDeterminer

    determiner = ConstituencyCountDeterminer()

    # Create a mock election with specific seat distribution
    election = MagicMock(spec=Election)
    election.electionConfig = MagicMock()
    election.electionConfig.constituency_representation = ConstituencyRepresentation.GOVERNING_MAJORITY
    election.electionConfig.quota_correction_strategy = QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES
    election.electionConfig.seed = 1

    # Test case 1: Three parties with 5 seats each
    seats = {
        'Party A': 5,
        'Party B': 5,
        'Party C': 5
    }
    election.getWinner.return_value = MagicMock()
    election.getWinner.return_value.getContainedParties.return_value = seats.keys()

    quotas = determiner.run(election, seats)

    # Calculate the quota sum
    quota_sum = sum(quotas.values())
    total_seats = sum(seats.values())
    expected_constituencies = total_seats // 2

    assert quota_sum == expected_constituencies, (
        f"Quota correction failed:\n"
        f"  Party seats: {seats}\n"
        f"  Party quotas (after correction): {quotas}\n"
        f"  Sum of quotas: {quota_sum}\n"
        f"  Number of constituencies needed: {expected_constituencies}\n"
        f"  Deficit: {expected_constituencies - quota_sum}"
    )

    # Additional test cases
    test_cases = [
        # (party_seats_dict, expected_old_deficit)
        ({'A': 5, 'B': 5, 'C': 5}, 1),           # Was: 6 < 7
        ({'A': 3, 'B': 3, 'C': 3, 'D': 3}, 2),   # Was: 4 < 6
        ({'A': 7, 'B': 7, 'C': 7}, 1),           # Was: 9 < 10
        ({'A': 1, 'B': 1, 'C': 1, 'D': 1}, 2),   # Was: 0 < 2
    ]

    for party_seats, expected_old_deficit in test_cases:
        # Mock getWinner to return all parties as government parties
        election.getWinner.return_value.getContainedParties.return_value = party_seats.keys()

        quotas = determiner.run(election, party_seats)
        quota_sum = sum(quotas.values())
        total_seats = sum(party_seats.values())
        expected_constituencies = total_seats // 2

        actual_deficit = expected_constituencies - quota_sum
        assert actual_deficit == 0, (
            f"Quota correction failed for {party_seats}:\n"
            f"  Party quotas: {quotas}\n"
            f"  Sum of quotas: {quota_sum}\n"
            f"  Expected constituencies: {expected_constituencies}\n"
            f"  Actual deficit: {actual_deficit} (should be 0)"
        )

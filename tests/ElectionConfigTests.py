import pytest
import pandas as pd
from ipres import ElectionConfig, ConstituenciesConfig, SeatDistributionMethod
from ipres.election_config import ConstituencyRepresentation
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def make_simple_cc(num_constituencies=10):
    """Helper to create a simple constituencies config."""
    df = pd.DataFrame({
        'constituency_name': [f"C{i}" for i in range(1, num_constituencies + 1)],
        'constituency_size': [10000] * num_constituencies,
    })
    return ConstituenciesConfig.from_dataframe(df)


def test_election_config_government_majority_percent_default():
    """Test default government majority is 55% (50% + 5% margin)"""
    cc = make_simple_cc(10)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )

    # Default margin is 5%, so government majority should be 55%
    assert config.getParliamentMajorityPercent() == 55.0
    assert config.parliamentMajorityMarginPercent == 5.0


def test_election_config_government_majority_percent_custom():
    """Test custom margin (e.g., 10% margin = 60% majority)"""
    cc = make_simple_cc(10)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(10.0, MarginUnit.PERCENT)
    )

    assert config.getParliamentMajorityPercent() == 60.0
    assert config.parliamentMajorityMarginPercent == 10.0


def test_election_config_government_majority_percent_zero():
    """Test zero margin (50% majority = simple majority)"""
    cc = make_simple_cc(10)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(0.0, MarginUnit.PERCENT)
    )

    assert config.getParliamentMajorityPercent() == 50.0
    assert config.parliamentMajorityMarginPercent == 0.0


def test_election_config_government_majority_seats_calculation():
    """Test seat calculation from percent with different parliamentary seats"""
    cc = make_simple_cc(50)  # 100 parliamentary seats (50 constituencies * 2)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(10.0, MarginUnit.PERCENT)
    )

    # 100 seats * 60% = 60 seats
    assert config.parliamentarySeats == 100
    assert config.getParliamentMajoritySeats() == 60


def test_election_config_government_majority_seats_rounding():
    """Test that seat calculation rounds up (ceil)"""
    cc = make_simple_cc(25)  # 50 parliamentary seats

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT)
    )

    # 50 seats * 55% = 27.5 → should round up to 28
    assert config.parliamentarySeats == 50
    assert config.getParliamentMajoritySeats() == 28


def test_election_config_government_majority_seats_mode():
    """Test government majority specified in seats instead of percent"""
    cc = make_simple_cc(50)  # 100 parliamentary seats

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(15, MarginUnit.SEATS)
    )

    assert config.parliamentarySeats == 100
    assert config.parliamentMajorityMarginSeats == 15
    # Margin of 15 seats = 15% of 100 seats
    assert config.parliamentMajorityMarginPercent == 15.0
    # Government majority = 50% + 15% = 65%
    assert config.getParliamentMajorityPercent() == 65.0
    # In seats: ceil(65% of 100) = 65 seats
    assert config.getParliamentMajoritySeats() == 65


def test_election_config_parliamentary_seats_entire_parliament():
    """Test parliamentary seats = constituencies * 2 (default mode)"""
    cc = make_simple_cc(50)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )

    # ENTIRE_PARLIAMENT mode: 50 constituencies * 2 = 100 seats
    assert config.parliamentarySeats == 100


def test_election_config_parliamentary_seats_different_constituency_counts():
    """Test parliamentary seats calculation with various constituency counts"""
    test_cases = [
        (1, 2),      # 1 constituency → 2 seats
        (10, 20),    # 10 constituencies → 20 seats
        (100, 200),  # 100 constituencies → 200 seats
        (299, 598),  # 299 constituencies → 598 seats (like Bundestag)
    ]

    for num_constituencies, expected_seats in test_cases:
        cc = make_simple_cc(num_constituencies)
        config = ElectionConfig(
            constituencies_config=cc,
            participating_parties=["A", "B"]
        )
        assert config.parliamentarySeats == expected_seats, \
            f"Expected {expected_seats} seats for {num_constituencies} constituencies"


def test_election_config_government_majority_specification_unit():
    """Test that we can query which unit (PERCENT or SEATS) is being used"""
    cc = make_simple_cc(10)

    # Default: PERCENT mode
    config1 = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )
    assert config1.parliamentMajoritySpecificationUnit == MarginUnit.PERCENT

    # SEATS mode
    config2 = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(10, MarginUnit.SEATS)
    )
    assert config2.parliamentMajoritySpecificationUnit == MarginUnit.SEATS


def test_election_config_with_different_distribution_methods():
    """Test that government majority works regardless of distribution method (now in ElectionEvaluator)"""
    cc = make_simple_cc(10)

    # ElectionConfig no longer has seat_distribution_method
    # But government majority calculation should still work
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )

    # Should work regardless of distribution method (which is now in ElectionEvaluator)
    assert config.getParliamentMajorityPercent() == 55.0
    assert config.getParliamentMajoritySeats() > 0


def test_election_uses_config_government_majority():
    """Test that Election correctly uses ElectionConfig's government majority"""
    from ipres import Election

    cc = make_simple_cc(5)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(20.0, MarginUnit.PERCENT),
        seed=123
    )

    election = Election(electionConfig=config)
    first_iteration = election.start()

    # The ballot uses the ballot majority threshold, not the parliament threshold
    assert first_iteration.getBallotMajorityPercent() == config.getBallotMajorityPercent()
    assert first_iteration.getBallotMajorityPercent() == 52.0  # default ballot_majority_margin = 2%


def test_election_config_frozen():
    """Test that ElectionConfig is immutable (frozen=True)"""
    cc = make_simple_cc(10)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )

    # Should not be able to modify frozen dataclass
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        config.participating_parties = ["X", "Y", "Z"]


def test_ballot_majority_percent_default():
    """Default ballot_majority_margin is 2%, giving a 52% threshold."""
    cc = make_simple_cc(10)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
    )
    assert config.getBallotMajorityPercent() == 52.0


def test_ballot_majority_percent_custom():
    """Custom ballot_majority_margin is applied correctly."""
    cc = make_simple_cc(10)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        ballot_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
    )
    assert config.getBallotMajorityPercent() == 55.0


def test_ballot_and_parliament_majority_are_independent():
    """ballot_majority_margin and parliament_majority_margin are independent values."""
    cc = make_simple_cc(10)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(10.0, MarginUnit.PERCENT),
        ballot_majority_margin=SuperMajorityMargin(3.0, MarginUnit.PERCENT),
    )
    assert config.getParliamentMajorityPercent() == 60.0
    assert config.getBallotMajorityPercent() == 53.0


def test_parliament_majority_margin_seats_from_percent():
    """parliamentMajorityMarginSeats with PERCENT margin must use ceil(seats * pct / 100).

    Mutant #884: * (pct/100) → / (pct/100) gives 100 / 0.1 = 1000.
    Mutant #885: * (pct/100) → * (pct*100) gives 100 * 1000 = 100000.
    Mutant #886: / 100.0 → / 101.0 gives ceil(100 * 10/101) = ceil(9.9) = 10 (same here,
    but with 101 constituencies / 1% margin: original = 3, mutant = 2).

    50 constituencies (100 seats), 10% margin: ceil(100 * 10/100) = 10.
    """
    cc = make_simple_cc(50)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(10.0, MarginUnit.PERCENT),
    )
    assert config.parliamentMajorityMarginSeats == 10


def test_parliament_majority_margin_seats_from_percent_101_constituencies():
    """Kills mutant #886 (/ 101.0 instead of / 100.0): ceil(202 * 1/101) = 2, not 3.

    101 constituencies (202 seats), 1% margin: ceil(202 * 1/100) = ceil(2.02) = 3.
    Mutant #886: ceil(202 * 1/101) = ceil(2.0) = 2.
    """
    cc = make_simple_cc(101)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(1.0, MarginUnit.PERCENT),
    )
    assert config.parliamentMajorityMarginSeats == 3


def test_parliament_majority_margin_percent_from_seats_unequal_case():
    """parliamentMajorityMarginPercent with SEATS margin must use 100 * value / seats.

    Mutant #883 inverts the unit check, taking the PERCENT branch (returns value=5.0).
    Here margin=5 SEATS with 20 total seats gives 5/20 * 100 = 25.0%, not 5.0%.
    """
    cc = make_simple_cc(10)  # 20 total seats
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(5, MarginUnit.SEATS),
    )
    assert config.parliamentMajorityMarginPercent == pytest.approx(25.0)


def test_ballot_majority_percent_from_seats():
    """getBallotMajorityPercent with SEATS margin uses 100 * value / seats.

    Mutant #894: 101.0 * value / seats → 50 + 10.1 = 60.1.
    Mutant #895: 100.0 / value / seats → 50 + 0.1 = 50.1.
    Mutant #896: 100.0 * value * seats → astronomically large.

    50 constituencies (100 seats), 10-seat ballot margin:
    50 + 100.0 * 10 / 100 = 60.0%.
    """
    cc = make_simple_cc(50)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        ballot_majority_margin=SuperMajorityMargin(10, MarginUnit.SEATS),
    )
    assert config.getBallotMajorityPercent() == pytest.approx(60.0)


def test_parliamentary_seats_governing_majority_with_adjustment():
    """parliamentarySeats for GOVERNING_MAJORITY uses P += 1 when ceil under-counts.

    Mutants #919–922 corrupt the P += 1 adjustment in _get_parliamentary_seats.

    C=11 constituencies, M=55% margin: P = int(200*11/105) = 20.
    ceil(105*20/100) = ceil(21.0) = 21 < 22 = 2*11 → P += 1 → P = 21.

    Mutant #920 (P = 1): parliamentarySeats = 1.
    Mutant #921 (P -= 1): parliamentarySeats = 19.
    Mutant #922 (P += 2): parliamentarySeats = 22.
    Mutant #919 (< 2/C = 0.18): 21 < 0.18 = False → no increment → parliamentarySeats = 20.
    """
    cc = make_simple_cc(11)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(55.0, MarginUnit.PERCENT),
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY,
    )
    assert config.parliamentarySeats == 21

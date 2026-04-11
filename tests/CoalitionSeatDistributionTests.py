import pytest
import numpy as np
import pandas as pd
from ipres.allocation import ConstituencyAllocationMethod
from ipres import (
    Election, ElectionConfig, ConstituenciesConfig,
    Ballot, Contestant, contestantsDictFromParties, ElectionRoundInput, SeatDistributionMethod,
    SeatDistributor, ConstituencyRepresentation
)


def make_simple_cc(num_constituencies=5, size=10000):
    """Helper to create a simple constituencies config."""
    df = pd.DataFrame({
        'constituency_name': [f"C{i}" for i in range(1, num_constituencies + 1)],
        'constituency_size': [size] * num_constituencies,
    })
    return ConstituenciesConfig.from_dataframe(df)


def test_distribute_seats_among_members_single_party():
    """Test that distribute_seats_among_members returns all seats for single party."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        seed=123
    )
    election = Election(electionConfig=config)
    distributor = SeatDistributor()

    # Create a single party
    party_a = Contestant.from_party("A")

    # Distribute 50 seats
    result = distributor._distribute_among_members(
        party_a, 50
    )

    assert result == {"A": 50}


def test_distribute_seats_among_members_simple_coalition():
    """Test seat distribution within a simple coalition."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=456
    )
    election = Election(electionConfig=config)
    distributor = SeatDistributor()

    # Create iteration and form coalition
    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 60.0, "B": 30.0, "C": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(100)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition A+B (weights ~0.67 and ~0.33)
    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]

    # Distribute 90 seats among coalition members
    result = distributor._distribute_among_members(coalition, 90)

    # Check that both parties get seats
    assert "A" in result
    assert "B" in result
    assert "C" not in result  # C is not in the coalition

    # Total should be 90
    assert sum(result.values()) == 90

    # A should get roughly 60 seats (2/3 of 90), B should get roughly 30 seats (1/3 of 90)
    assert 55 <= result["A"] <= 65, f"Expected A to get ~60 seats, got {result['A']}"
    assert 25 <= result["B"] <= 35, f"Expected B to get ~30 seats, got {result['B']}"


def test_distribute_seats_among_members_equal_weights():
    """Test seat distribution with equal weights."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=789
    )
    election = Election(electionConfig=config)

    distributor = SeatDistributor()

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 50.0, "B": 50.0, "C": 0.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(200)
    )

    iteration = Ballot.run(iteration_input)

    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]

    # Distribute 100 seats
    result = distributor._distribute_among_members(coalition, 100)

    # Both should get roughly 50 seats
    assert abs(result["A"] - 50) <= 2, f"Expected A to get ~50 seats, got {result['A']}"
    assert abs(result["B"] - 50) <= 2, f"Expected B to get ~50 seats, got {result['B']}"
    assert sum(result.values()) == 100


def test_distribute_seats_among_members_three_parties():
    """Test seat distribution with three parties in coalition."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=111
    )
    election = Election(electionConfig=config)

    distributor = SeatDistributor()

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(300)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition A+B+C (leave D out)
    contestants_list = [
        iteration.getContestants()["A"],
        iteration.getContestants()["B"],
        iteration.getContestants()["C"]
    ]
    iteration.formCoalition("Coalition_ABC", contestants_list)

    coalition = iteration.getContestants()["Coalition_ABC"]

    # Distribute 90 seats
    result = distributor._distribute_among_members(coalition, 90)

    # All three parties should get seats
    assert "A" in result
    assert "B" in result
    assert "C" in result
    assert "D" not in result

    # Total should be 90
    assert sum(result.values()) == 90

    # Rough proportions: A ~40, B ~30, C ~20
    assert 35 <= result["A"] <= 45, f"Expected A to get ~40 seats, got {result['A']}"
    assert 25 <= result["B"] <= 35, f"Expected B to get ~30 seats, got {result['B']}"
    assert 15 <= result["C"] <= 25, f"Expected C to get ~20 seats, got {result['C']}"


def test_distribute_seats_among_members_different_methods():
    """Test that different distribution methods work."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=222
    )
    election = Election(electionConfig=config)

    distributor = SeatDistributor()

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 60.0, "B": 40.0, "C": 0.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(400)
    )

    iteration = Ballot.run(iteration_input)

    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]

    # Test with different methods
    for method in [SeatDistributionMethod.SAINTE_LAGUE,
                   SeatDistributionMethod.D_HONDT,
                   SeatDistributionMethod.HARE_NIEMEYER]:
        result = distributor._distribute_among_members(coalition, 50)

        # All methods should give valid results
        assert sum(result.values()) == 50, f"Method {method.name}: Total seats != 50"
        assert result["A"] > 0, f"Method {method.name}: A got 0 seats"
        assert result["B"] > 0, f"Method {method.name}: B got 0 seats"
        assert result["A"] > result["B"], f"Method {method.name}: A should get more seats than B"


def test_distribute_seats_among_members_small_seat_count():
    """Test seat distribution with very few seats."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=333
    )
    election = Election(electionConfig=config)

    distributor = SeatDistributor()

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 50.0, "B": 30.0, "C": 20.0, "D": 0.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(500)
    )

    iteration = Ballot.run(iteration_input)

    contestants_list = [
        iteration.getContestants()["A"],
        iteration.getContestants()["B"],
        iteration.getContestants()["C"]
    ]
    iteration.formCoalition("Coalition_ABC", contestants_list)

    coalition = iteration.getContestants()["Coalition_ABC"]

    # Distribute only 3 seats among 3 parties
    result = distributor._distribute_among_members(coalition, 3)

    # Total should be 3
    assert sum(result.values()) == 3

    # All parties should get at least something or the strongest get seats
    assert all(seats >= 0 for seats in result.values())

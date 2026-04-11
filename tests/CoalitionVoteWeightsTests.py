import pytest
import numpy as np
import pandas as pd
from ipres import (
    contestantsDictFromParties,
    Election, ElectionConfig, ConstituenciesConfig,
    Ballot, Contestant, ElectionRoundInput
)


def make_simple_cc(num_constituencies=5, size=10000):
    """Helper to create a simple constituencies config."""
    df = pd.DataFrame({
        'constituency_name': [f"C{i}" for i in range(1, num_constituencies + 1)],
        'constituency_size': [size] * num_constituencies,
    })
    return ConstituenciesConfig.from_dataframe(df)


def test_coalition_vote_weights_basic():
    """Test that vote weights are calculated correctly for a simple coalition."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=123
    )
    election = Election(electionConfig=config)

    # Create iteration with specific vote probabilities
    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 50.0, "B": 30.0, "C": 20.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(100)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition between A and B
    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    # Get the coalition
    coalition = iteration.getContestants()["Coalition_AB"]

    # Check that coalition has vote weights
    assert coalition.isCoalition()
    assert "A" in coalition.member_vote_weights
    assert "B" in coalition.member_vote_weights

    # Vote weights should be proportional to original votes (A had 50%, B had 30%)
    # Within coalition: A = 50/(50+30) = 0.625, B = 30/(50+30) = 0.375
    # But actual votes vary slightly due to random sampling
    weight_a = coalition.getMemberVoteWeight("A")
    weight_b = coalition.getMemberVoteWeight("B")

    assert abs(weight_a - 0.625) < 0.01, f"Expected A weight ~0.625, got {weight_a}"
    assert abs(weight_b - 0.375) < 0.01, f"Expected B weight ~0.375, got {weight_b}"

    # Weights should sum to 1.0
    assert abs(weight_a + weight_b - 1.0) < 0.0001


def test_coalition_vote_weights_equal_votes():
    """Test vote weights when members have equal votes."""
    cc = make_simple_cc(3, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=456
    )
    election = Election(electionConfig=config)

    # Create iteration with equal probabilities
    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 40.0, "B": 40.0, "C": 20.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(200)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition between A and B (equal votes)
    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]

    # Both should have ~0.5 weight (allowing for random variation)
    weight_a = coalition.getMemberVoteWeight("A")
    weight_b = coalition.getMemberVoteWeight("B")

    assert abs(weight_a - 0.5) < 0.01, f"Expected A weight ~0.5, got {weight_a}"
    assert abs(weight_b - 0.5) < 0.01, f"Expected B weight ~0.5, got {weight_b}"


def test_coalition_vote_weights_three_members():
    """Test vote weights with three coalition members."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=789
    )
    election = Election(electionConfig=config)

    # Create iteration
    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(300)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition with A, B, C (total 90%)
    contestants_list = [
        iteration.getContestants()["A"],
        iteration.getContestants()["B"],
        iteration.getContestants()["C"]
    ]
    iteration.formCoalition("Coalition_ABC", contestants_list)

    coalition = iteration.getContestants()["Coalition_ABC"]

    # Within coalition: A = 40/90 = 0.4444, B = 30/90 = 0.3333, C = 20/90 = 0.2222
    # Allowing for random variation
    weight_a = coalition.getMemberVoteWeight("A")
    weight_b = coalition.getMemberVoteWeight("B")
    weight_c = coalition.getMemberVoteWeight("C")

    assert abs(weight_a - 0.4444) < 0.01, f"Expected A weight ~0.4444, got {weight_a}"
    assert abs(weight_b - 0.3333) < 0.01, f"Expected B weight ~0.3333, got {weight_b}"
    assert abs(weight_c - 0.2222) < 0.01, f"Expected C weight ~0.2222, got {weight_c}"

    # Weights should sum to 1.0
    assert abs(weight_a + weight_b + weight_c - 1.0) < 0.0001


def test_get_member_vote_weight_single_party_raises():
    """Test that getMemberVoteWeight raises error for single party."""
    party = Contestant.from_party("A")

    with pytest.raises(ValueError, match="not a coalition"):
        party.getMemberVoteWeight("A")


def test_get_member_vote_weight_invalid_member_raises():
    """Test that getMemberVoteWeight raises error for non-existent member."""
    cc = make_simple_cc(3, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=111
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 50.0, "B": 30.0, "C": 20.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(400)
    )

    iteration = Ballot.run(iteration_input)
    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]

    # C is not in the coalition
    with pytest.raises(ValueError, match="not a member"):
        coalition.getMemberVoteWeight("C")


def test_coalition_vote_weights_persist_across_iterations():
    """Test that coalition vote weights persist when coalition continues to next iteration."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=222
    )
    election = Election(electionConfig=config)

    # First iteration
    iteration1_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 50.0, "B": 30.0, "C": 20.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(500)
    )

    iteration1 = Ballot.run(iteration1_input)

    # Form coalition
    contestants_list = [iteration1.getContestants()["A"], iteration1.getContestants()["B"]]
    iteration1.formCoalition("Coalition_AB", contestants_list)

    coalition1 = iteration1.getContestants()["Coalition_AB"]
    weight_a_iter1 = coalition1.getMemberVoteWeight("A")
    weight_b_iter1 = coalition1.getMemberVoteWeight("B")

    # Create next iteration with the coalition
    if not iteration1.hasWinner():
        iteration2_input = iteration1.getNextElectionRoundInput()
        iteration2 = Ballot.run(iteration2_input)

        # Coalition should still exist with same weights
        if "Coalition_AB" in iteration2.getContestants():
            coalition2 = iteration2.getContestants()["Coalition_AB"]

            # Weights should be identical
            assert coalition2.getMemberVoteWeight("A") == weight_a_iter1
            assert coalition2.getMemberVoteWeight("B") == weight_b_iter1


def test_coalition_vote_weights_uses_original_votes():
    """Test that vote weights are calculated from original votes, not after other coalitions."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=333
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(600)
    )

    iteration = Ballot.run(iteration_input)

    # Form first coalition C+D
    contestants_cd = [iteration.getContestants()["C"], iteration.getContestants()["D"]]
    iteration.formCoalition("Coalition_CD", contestants_cd)

    # Now form second coalition A+B
    # This should use ORIGINAL votes, not votes after CD coalition
    contestants_ab = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_ab)

    coalition_ab = iteration.getContestants()["Coalition_AB"]

    # Weights should be based on original 40% and 30% (not affected by CD coalition)
    # A = 40/(40+30) = 0.5714, B = 30/(40+30) = 0.4286
    # Allowing for random variation
    weight_a = coalition_ab.getMemberVoteWeight("A")
    weight_b = coalition_ab.getMemberVoteWeight("B")

    assert abs(weight_a - 0.5714) < 0.01, f"Expected A weight ~0.5714, got {weight_a}"
    assert abs(weight_b - 0.4286) < 0.01, f"Expected B weight ~0.4286, got {weight_b}"


def test_get_member_vote_weights_for_parties_single_party():
    """Test getMemberVoteWeightsForParties for single party."""
    party = Contestant.from_party("A")

    weights = party.getMemberVoteWeightsForParties()

    assert weights == {"A": 1.0}


def test_get_member_vote_weights_for_parties_simple_coalition():
    """Test getMemberVoteWeightsForParties for simple coalition."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=444
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C"]),
        probabilities={"A": 60.0, "B": 30.0, "C": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(700)
    )

    iteration = Ballot.run(iteration_input)

    # Form coalition A+B (60% + 30% = 90% total)
    contestants_list = [iteration.getContestants()["A"], iteration.getContestants()["B"]]
    iteration.formCoalition("Coalition_AB", contestants_list)

    coalition = iteration.getContestants()["Coalition_AB"]
    weights = coalition.getMemberVoteWeightsForParties()

    # Should have weights for A and B (not C, which is outside coalition)
    assert "A" in weights
    assert "B" in weights
    assert "C" not in weights

    # A should have ~2/3 weight, B should have ~1/3 weight
    assert abs(weights['A'] - 0.6667) < 0.01, f"Expected A weight ~0.6667, got {weights['A']}"
    assert abs(weights['B'] - 0.3333) < 0.01, f"Expected B weight ~0.3333, got {weights['B']}"

    # Should sum to 1.0
    assert abs(sum(weights.values()) - 1.0) < 0.0001


def test_coalition_of_same_iteration_coalition_and_party():
    """Test forming a coalition from a same-iteration coalition and a single party."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=777
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(1000)
    )

    iteration = Ballot.run(iteration_input)

    # Form first coalition: A+B
    iteration.formCoalition("Coalition_AB", ["A", "B"])

    # Form coalition of Coalition_AB with C — should now be allowed
    iteration.formCoalition("Coalition_ABC", ["Coalition_AB", "C"])

    coalition_abc = iteration.getContestants()["Coalition_ABC"]
    assert coalition_abc.isCoalition()
    assert set(coalition_abc.getMemberNames()) == {"Coalition_AB", "C"}

    # Weights relative to total AB+C votes: AB = (40+30)=70, C = 20 → AB=0.7778, C=0.2222
    weight_ab = coalition_abc.getMemberVoteWeight("Coalition_AB")
    weight_c = coalition_abc.getMemberVoteWeight("C")
    assert abs(weight_ab - 0.7778) < 0.01, f"Expected AB weight ~0.7778, got {weight_ab}"
    assert abs(weight_c - 0.2222) < 0.01, f"Expected C weight ~0.2222, got {weight_c}"
    assert abs(weight_ab + weight_c - 1.0) < 0.0001

    # getMemberVoteWeightsForParties should recursively resolve to A, B, C
    party_weights = coalition_abc.getMemberVoteWeightsForParties()
    assert set(party_weights.keys()) == {"A", "B", "C"}
    assert abs(sum(party_weights.values()) - 1.0) < 0.0001


def test_coalition_of_same_iteration_coalitions_vote_weights():
    """Test forming a coalition from two same-iteration coalitions (ABCD = AB + CD)."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D", "E"],
        seed=888
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D", "E"]),
        probabilities={"A": 30.0, "B": 20.0, "C": 25.0, "D": 15.0, "E": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(2000)
    )

    iteration = Ballot.run(iteration_input)

    # Form AB and CD in same iteration
    iteration.formCoalition("Coalition_AB", ["A", "B"])
    iteration.formCoalition("Coalition_CD", ["C", "D"])

    # Now form super-coalition of both same-iteration coalitions
    iteration.formCoalition("Coalition_ABCD", ["Coalition_AB", "Coalition_CD"])

    coalition_abcd = iteration.getContestants()["Coalition_ABCD"]
    assert coalition_abcd.isCoalition()

    # AB had 50 votes total, CD had 40 → AB=0.5556, CD=0.4444
    weight_ab = coalition_abcd.getMemberVoteWeight("Coalition_AB")
    weight_cd = coalition_abcd.getMemberVoteWeight("Coalition_CD")
    assert abs(weight_ab - 0.5556) < 0.01, f"Expected AB weight ~0.5556, got {weight_ab}"
    assert abs(weight_cd - 0.4444) < 0.01, f"Expected CD weight ~0.4444, got {weight_cd}"
    assert abs(weight_ab + weight_cd - 1.0) < 0.0001

    # All four parties should appear in the recursive party weights
    party_weights = coalition_abcd.getMemberVoteWeightsForParties()
    assert set(party_weights.keys()) == {"A", "B", "C", "D"}
    assert abs(sum(party_weights.values()) - 1.0) < 0.0001


def test_deep_nested_coalition_vote_weights():
    """Test three-level nesting: ((A+B)+C)+D within a single iteration."""
    cc = make_simple_cc(5, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D", "E"],
        seed=999
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D", "E"]),
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0, "E": 0.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(3000)
    )

    iteration = Ballot.run(iteration_input)

    # Level 1: A+B
    iteration.formCoalition("AB", ["A", "B"])
    # Level 2: (A+B)+C
    iteration.formCoalition("ABC", ["AB", "C"])
    # Level 3: ((A+B)+C)+D
    iteration.formCoalition("ABCD", ["ABC", "D"])

    coalition_abcd = iteration.getContestants()["ABCD"]
    assert coalition_abcd.isCoalition()

    # Weights at top level: ABC had 90 votes, D had 10 → ABC=0.9, D=0.1
    weight_abc = coalition_abcd.getMemberVoteWeight("ABC")
    weight_d = coalition_abcd.getMemberVoteWeight("D")
    assert abs(weight_abc - 0.9) < 0.01, f"Expected ABC weight ~0.9, got {weight_abc}"
    assert abs(weight_d - 0.1) < 0.01, f"Expected D weight ~0.1, got {weight_d}"

    # All parties should appear in recursive resolution
    party_weights = coalition_abcd.getMemberVoteWeightsForParties()
    assert set(party_weights.keys()) == {"A", "B", "C", "D"}
    assert abs(sum(party_weights.values()) - 1.0) < 0.0001


def test_coalition_of_same_iteration_coalition_zero_votes():
    """Test vote weights when a same-iteration coalition's parties all have zero votes."""
    cc = make_simple_cc(2, 10000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],
        seed=555
    )
    election = Election(electionConfig=config)

    iteration_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D"]),
        probabilities={"A": 0.0, "B": 0.0, "C": 70.0, "D": 30.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(4000)
    )

    iteration = Ballot.run(iteration_input)

    # A and B both have zero votes
    iteration.formCoalition("AB", ["A", "B"])
    # AB has 0 effective votes; C has real votes → weight_C ≈ 1.0, weight_AB ≈ 0.0
    iteration.formCoalition("ABC", ["AB", "C"])

    coalition_abc = iteration.getContestants()["ABC"]
    weight_ab = coalition_abc.getMemberVoteWeight("AB")
    weight_c = coalition_abc.getMemberVoteWeight("C")

    assert abs(weight_c - 1.0) < 0.01, f"Expected C weight ~1.0, got {weight_c}"
    assert abs(weight_ab - 0.0) < 0.01, f"Expected AB weight ~0.0, got {weight_ab}"

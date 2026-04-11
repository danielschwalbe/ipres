import math
import numpy as np
import pandas as pd
import pytest
from ipres import (
    Ballot, ElectionRoundInput, Contestant,
    contestantsFromParties, contestantsDictFromParties,
    ConstituenciesConfig, DrawLotsStrategy, VoteMatrix
)
from ipres.election import Election
from ipres.election_config import ElectionConfig

def make_simple_cc(size=1000):
    df = pd.DataFrame({
        'constituency_name': ["C1"],
        'constituency_size': [size],
    })
    return ConstituenciesConfig.from_dataframe(df)

def make_mock_election(cc: ConstituenciesConfig) -> Election:
    """Create a minimal mock Election object for testing."""
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=42
    )
    return Election(electionConfig=config)

def test_round_input_init():
    cc = make_simple_cc()
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    ri = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities={"A": 60.0, "B": 40.0},
        ballot_majority_percent=51.0
    )
    assert ri.numberOfContestants() == 2
    assert ri.ballot_majority_percent == 51.0
    assert ri.draw_lots_strategy == DrawLotsStrategy.RANDOM

def test_ballot_run_winner():
    # Scenario: A wins immediately with 60%
    cc = make_simple_cc(10_000)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    ri = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities={"A": 60.0, "B": 40.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(42)
    )

    ballot = Ballot.run(ri)

    assert ballot.hasWinner() is True
    assert ballot._winner.name == "A"
    assert ballot.hasNext() is False
    assert ballot.needsDecisionByLotInNextRound() is False
    assert ballot.vote_matrix is not None

    votes = ballot.getContestantsVotesAfterPossibleCoalitions()
    assert votes["A"] > votes["B"]
    assert math.isclose(votes.sum(), 10000, abs_tol=1)

def test_ballot_run_next_round():
    # Scenario: No one reaches 55%, so next round is needed
    cc = make_simple_cc(10_000)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    ri = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(42)
    )

    ballot = Ballot.run(ri)

    assert ballot.hasWinner() is False
    assert ballot.hasNext() is True

    next_ri = ballot.getNextRoundInput()
    assert next_ri.previousRound == ballot
    # A (40) + B (35) = 75 > 66.6, so C should be dropped.
    assert "A" in next_ri.contestants
    assert "B" in next_ri.contestants
    assert "C" not in next_ri.contestants

def test_coalition_formation_and_votes():
    cc = make_simple_cc(10_000)
    election = make_mock_election(cc)
    contestants_list = contestantsFromParties(["A", "B", "C"])
    contestants_dict = {c.name: c for c in contestants_list}
    ri = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants_dict,
        probabilities={"A": 30.0, "B": 25.0, "C": 45.0},
        turnout=100.0,
        rng=np.random.default_rng(42)
    )

    ballot = Ballot.run(ri)

    party_a = ballot.getContestants()["A"]
    party_b = ballot.getContestants()["B"]
    ballot.formCoalition("Coalition_AB", [party_a, party_b])

    current_contestants = ballot.getContestants()
    assert "Coalition_AB" in current_contestants
    assert "A" not in current_contestants
    assert "B" not in current_contestants
    assert "C" in current_contestants

    votes = ballot.getContestantsVotesAfterPossibleCoalitions()
    assert votes["Coalition_AB"] > votes["C"]
    assert math.isclose(votes["Coalition_AB"], 5500, abs_tol=200)

    ballot.resetCoalitions()
    assert "A" in ballot.getContestants()
    assert "Coalition_AB" not in ballot.getContestants()

def test_decide_by_lot_marginal_lead():
    cc = make_simple_cc(10_000)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])

    ri1 = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities={"A": 50.0, "B": 50.0},
        draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD,
        rng=np.random.default_rng(42)
    )

    ballot1 = Ballot.run(ri1)
    assert ballot1.hasWinner() is False

    ri2 = ballot1.getNextRoundInput()
    ri2.probabilities = {"A": 50.5, "B": 49.5}
    ri2.ballot_majority_percent = 55.0

    ballot2 = Ballot.run(ri2)
    assert ballot2.needsDecisionByLotInNextRound() is True

    from ipres import ElectionRound, DrawOfLots
    lot = ElectionRound.run(ballot2.getNextRoundInput())

    assert lot.getWinner().name == "A"

def test_get_contestants_by_percentage_desc_with_threshold():
    cc = make_simple_cc(10_000)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C", "D"])
    ri = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities={"A": 40.0, "B": 30.0, "C": 20.0, "D": 10.0},
        turnout=100.0,
        rng=np.random.default_rng(42)
    )
    ballot = Ballot.run(ri)

    res = ballot.getContestantsByPercentageDesc(threshold=60.0)
    assert list(res.index) == ["A", "B"]

    res = ballot.getContestantsByPercentageDesc(threshold=10.0)
    assert list(res.index) == ["A"]

def test_lot_needed_logic():
    cc = make_simple_cc(50_000)  # large enough that 50/50 never yields 55%
    election = make_mock_election(cc)
    contestants2 = contestantsDictFromParties(["A", "B"])

    ri1 = ElectionRoundInput(
        election=election, constituencies_config=cc, contestants=contestants2,
        probabilities={"A": 50.0, "B": 50.0}, rng=np.random.default_rng(1)
    )
    ballot1 = Ballot.run(ri1)
    assert ballot1.hasWinner() is False
    # First time with 2 contestants -> lot NOT needed (next round would be)
    assert ballot1.needsDecisionByLotInNextRound() is False

    ri2 = ballot1.getNextRoundInput()
    ri2.probabilities = {"A": 50.0, "B": 50.0}  # keep below threshold
    ballot2 = Ballot.run(ri2)
    assert ballot2.hasWinner() is False
    # Second time with 2 contestants -> lot needed in next round
    assert ballot2.needsDecisionByLotInNextRound() is True

def test_show_results_table_and_plot():
    cc = make_simple_cc(1000)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    ri = ElectionRoundInput(
        election=election, constituencies_config=cc, contestants=contestants,
        probabilities=[60, 40], turnout=100, rng=np.random.default_rng(1)
    )
    ballot = Ballot.run(ri)

    df = ballot.show_results_table(styler=False)
    assert isinstance(df, pd.DataFrame)
    assert "Stimmen" in df.columns
    assert "Prozent" in df.columns

    fig = ballot.plot_vote_share_pie()
    import matplotlib.figure
    assert isinstance(fig, matplotlib.figure.Figure)

def test_form_coalition_errors():
    cc = make_simple_cc(100)
    election = make_mock_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    ri = ElectionRoundInput(
        election=election, constituencies_config=cc, contestants=contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0}, rng=np.random.default_rng(1)
    )
    ballot = Ballot.run(ri)

    with pytest.raises(ValueError, match="Not among the contestants"):
        ballot.formCoalition("AB", [Contestant.from_party("A"), Contestant.from_party("Z")])

    with pytest.raises(ValueError, match="At least two contestants must compete"):
        ballot.formCoalition("ABC", [Contestant.from_party("A"), Contestant.from_party("B"), Contestant.from_party("C")])

def test_lot_required_logic():
    """Test ElectionRound._lot_required() across two-contestant chains."""
    from ipres import ElectionRound
    cc = make_simple_cc(100)
    election = make_mock_election(cc)
    contestants_abc = contestantsDictFromParties(["A", "B", "C"])
    contestants_ab = contestantsDictFromParties(["A", "B"])

    # No previous round -> lot not required
    ri1 = ElectionRoundInput(
        election=election, constituencies_config=cc, contestants=contestants_abc,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0}, rng=np.random.default_rng(1)
    )
    ballot1 = Ballot.run(ri1)
    assert ElectionRound._lot_required(ballot1.getNextRoundInput()) is False

    # Two identical two-contestant rounds -> lot required on the third
    # Use an explicit ballot threshold of 55% so random 50/50 votes never cross it
    ri_ab1 = ElectionRoundInput(
        election=election, constituencies_config=cc, contestants=contestants_ab,
        probabilities={"A": 50.0, "B": 50.0}, rng=np.random.default_rng(2),
        ballot_majority_percent=55.0,
    )
    ballot_ab1 = Ballot.run(ri_ab1)
    assert ballot_ab1.hasWinner() is False

    ri_ab2 = ballot_ab1.getNextRoundInput()
    ri_ab2.probabilities = {"A": 50.0, "B": 50.0}  # keep below threshold
    ballot_ab2 = Ballot.run(ri_ab2)
    assert ballot_ab2.hasWinner() is False
    assert ElectionRound._lot_required(ballot_ab2.getNextRoundInput()) is True

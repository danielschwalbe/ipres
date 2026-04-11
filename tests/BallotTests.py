import numpy as np
import pandas as pd
import pytest

from ipres import (
    Ballot, ElectionRound, ElectionRoundInput, DrawLotsStrategy,
    Contestant, contestantsFromParties, contestantsDictFromParties,
    ConstituenciesConfig, VoteMatrix,
)
from ipres.election import Election
from ipres.election_config import ElectionConfig


def make_cc(size: int = 10_000) -> ConstituenciesConfig:
    df = pd.DataFrame({
        "constituency_name": ["C1"],
        "constituency_size": [size],
    })
    return ConstituenciesConfig.from_dataframe(df)


def make_election(cc: ConstituenciesConfig) -> Election:
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=42,
    )
    return Election(electionConfig=config)


def make_input(cc, election, contestants, **kwargs) -> ElectionRoundInput:
    return ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        **kwargs,
    )


# ---- Basic lifecycle ----

def test_ballot_run_produces_winner_when_super_majority_reached():
    cc = make_cc(10_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 70.0, "B": 30.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(1),
    )
    ballot = Ballot.run(_input)

    assert ballot.hasWinner()
    assert ballot.getWinner().name == "A"
    assert not ballot.hasNext()
    assert ballot.getNextRoundInput() is None


def test_ballot_run_no_winner_provides_next_input():
    cc = make_cc(10_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(42),
    )
    ballot = Ballot.run(_input)

    assert not ballot.hasWinner()
    assert ballot.hasNext()
    next_inp = ballot.getNextRoundInput()
    assert next_inp is not None
    assert isinstance(next_inp, ElectionRoundInput)
    assert next_inp.previousRound is ballot


def test_ballot_round_number_increments():
    cc = make_cc(5_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(7),
        round_number=0,
    )
    ballot = Ballot.run(_input)
    assert ballot.getRoundNumber() == 1


def test_ballot_is_election_round_subtype():
    cc = make_cc(5_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 70.0, "B": 30.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(0),
    )
    ballot = Ballot.run(_input)
    assert isinstance(ballot, ElectionRound)
    assert ballot.wasDecidedByLot() is False


def test_ballot_registers_with_election():
    cc = make_cc(5_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 70.0, "B": 30.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(0),
    )
    Ballot.run(_input)
    assert election.getNumberOfIterations() == 1


# ---- Vote injection ----

def test_ballot_vote_matrix_injection():
    cc = make_cc()
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    # Build a fixed VoteMatrix and inject it
    pre_built = VoteMatrix.generate(
        cc,
        contestantsFromParties(["A", "B"]),
        probabilities={"A": 60.0, "B": 40.0},
        rng=np.random.default_rng(99),
        turnout=100.0,
    )
    _input = make_input(
        cc, election, contestants,
        ballot_majority_percent=55.0,
        vote_matrix=pre_built,
        rng=np.random.default_rng(0),
    )
    ballot = Ballot.run(_input)
    assert ballot._vote_matrix.getVotes().equals(pre_built.getVotes())


# ---- Previous round chain ----

def test_ballot_previous_round_is_none_for_first_round():
    cc = make_cc()
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(1),
    )
    ballot = Ballot.run(_input)
    assert ballot.getPreviousRound() is None


def test_ballot_previous_round_chain():
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(5),
    )
    ballot1 = Ballot.run(_input)

    if ballot1.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner; adjust probabilities.")

    next_inp = ballot1.getNextRoundInput()
    ballot2 = Ballot.run(next_inp)

    assert ballot2.getPreviousRound() is ballot1
    assert ballot2.getFirstRound() is ballot1


# ---- Coalition ----

def test_ballot_form_coalition_updates_result():
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 25.0, "C": 35.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(10),
    )
    ballot = Ballot.run(_input)

    if ballot.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    ballot.formCoalition("A+B", ["A", "B"])
    assert "A+B" in ballot.getContestants()
    assert "A" not in ballot.getContestants()
    assert "B" not in ballot.getContestants()


def test_ballot_reset_coalitions():
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 25.0, "C": 35.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(10),
    )
    ballot = Ballot.run(_input)

    if ballot.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    ballot.formCoalition("A+B", ["A", "B"])
    ballot.resetCoalitions()
    assert set(ballot.getContestants()) == {"A", "B", "C"}


def test_ballot_all_coalition_raises_in_round1():
    """Merging all contestants into a coalition is always forbidden in round 1."""
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(10),
    )
    ballot = Ballot.run(_input)
    if ballot.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    with pytest.raises(ValueError, match="All contestants cannot form a single coalition"):
        ballot.formCoalition("A+B+C", ["A", "B", "C"])


def test_ballot_all_coalition_raises_when_no_elimination_occurred():
    """Merging all contestants is forbidden when no party has ever been eliminated."""
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 52.0, "B": 48.0},
        turnout=100.0,
        ballot_majority_percent=60.0,
        rng=np.random.default_rng(5),
    )
    ballot1 = Ballot.run(_input)
    if ballot1.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    ballot2 = Ballot.run(ballot1.getNextRoundInput())

    with pytest.raises(ValueError, match="All contestants cannot form a single coalition"):
        ballot2.formCoalition("A+B", ["A", "B"])


def test_ballot_all_coalition_allowed_after_elimination():
    """Merging all remaining contestants is allowed once the field has been narrowed."""
    cc = make_cc(50_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 55.0, "B": 30.0, "C": 15.0},
        turnout=100.0,
        ballot_majority_percent=60.0,
        rng=np.random.default_rng(42),
    )
    ballot1 = Ballot.run(_input)
    if ballot1.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    next_inp = ballot1.getNextRoundInput()
    if set(next_inp.contestants.keys()) != {"A", "B"}:
        pytest.skip("C was not eliminated as expected.")

    ballot2 = Ballot.run(next_inp)

    # Must not raise: C was eliminated, so the field was narrowed
    ballot2.formCoalition("A+B", list(ballot2.getContestants().keys()))
    assert "A+B" in ballot2.getContestants()


# ---- ElectionRound.run() factory ----

def test_election_round_run_creates_ballot():
    cc = make_cc(10_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B", "C"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 40.0, "B": 35.0, "C": 25.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(2),
    )
    result = ElectionRound.run(_input)
    assert isinstance(result, Ballot)

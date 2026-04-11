import numpy as np
import pandas as pd
import pytest

from ipres import (
    Ballot, DrawOfLots, ElectionRound, ElectionRoundInput, DrawLotsStrategy,
    contestantsDictFromParties, ConstituenciesConfig, VoteMatrix,
)
from ipres.election import Election
from ipres.election_config import ElectionConfig


def make_cc(size: int = 50_000) -> ConstituenciesConfig:
    df = pd.DataFrame({
        "constituency_name": ["C1"],
        "constituency_size": [size],
    })
    return ConstituenciesConfig.from_dataframe(df)


def make_election(cc: ConstituenciesConfig) -> Election:
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        seed=42,
    )
    return Election(electionConfig=config)


def _run_two_identical_ballots(cc, election, probs, rng_seed) -> Ballot:
    """Run two ballot rounds with the same two contestants and return the second ballot."""
    contestants = contestantsDictFromParties(["A", "B"])
    inp1 = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        probabilities=probs,
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(rng_seed),
        draw_lots_strategy=DrawLotsStrategy.RANDOM,
    )
    ballot1 = Ballot.run(inp1)
    assert not ballot1.hasWinner(), "ballot1 must not have a winner for the test to proceed"

    inp2 = ballot1.getNextRoundInput()
    inp2.probabilities = probs  # keep same share → same contestant set likely
    ballot2 = Ballot.run(inp2)
    assert not ballot2.hasWinner(), "ballot2 must not have a winner for the test to proceed"
    return ballot2


def _lot_input_from(ballot2: Ballot, strategy: DrawLotsStrategy) -> ElectionRoundInput:
    """Build the ElectionRoundInput for a DrawOfLots round following ballot2."""
    inp = ballot2.getNextRoundInput()
    inp.draw_lots_strategy = strategy
    return inp


# ---- Basic properties ----

def test_draw_of_lots_always_has_winner():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=1)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)
    lot_inp.rng = np.random.default_rng(99)

    draw = DrawOfLots.run(lot_inp)

    assert draw.hasWinner()
    assert draw.getWinner() is not None
    assert draw.getWinner().name in ("A", "B")


def test_draw_of_lots_is_terminal():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=2)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    draw = DrawOfLots.run(lot_inp)

    assert draw.hasNext() is False
    assert draw.getNextRoundInput() is None


def test_draw_of_lots_decided_by_lot():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=3)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    draw = DrawOfLots.run(lot_inp)

    assert draw.wasDecidedByLot() is True


def test_draw_of_lots_is_election_round_subtype():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=4)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    draw = DrawOfLots.run(lot_inp)

    assert isinstance(draw, ElectionRound)


def test_draw_of_lots_registers_with_election():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=5)
    rounds_before = election.getNumberOfIterations()

    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)
    DrawOfLots.run(lot_inp)

    assert election.getNumberOfIterations() == rounds_before + 1


# ---- Vote delegation ----

def test_draw_of_lots_delegates_votes_to_previous_round():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=6)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    draw = DrawOfLots.run(lot_inp)

    expected = ballot2.getContestantsVotesAfterPossibleCoalitions()
    actual = draw.getContestantsVotesAfterPossibleCoalitions()
    assert expected.equals(actual)


def test_draw_of_lots_previous_round_is_ballot():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=7)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    draw = DrawOfLots.run(lot_inp)

    assert draw.getPreviousRound() is ballot2


# ---- Strategy: MARGINAL_LEAD ----

def test_marginal_lead_picks_higher_vote_getter():
    cc = make_cc()
    election = make_election(cc)
    # A gets ~52%, B ~48% — below the 55% threshold, so no winner in either ballot
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 52.0, "B": 48.0}, rng_seed=8)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.MARGINAL_LEAD)

    draw = DrawOfLots.run(lot_inp)

    votes = draw.getContestantsVotesAfterPossibleCoalitions()
    expected_winner = votes.idxmax()
    assert draw.getWinner().name == expected_winner


# ---- ElectionRound.run() routes to DrawOfLots ----

def test_election_round_run_creates_draw_of_lots_when_lot_required():
    cc = make_cc()
    election = make_election(cc)
    ballot2 = _run_two_identical_ballots(cc, election, {"A": 50.0, "B": 50.0}, rng_seed=9)
    lot_inp = _lot_input_from(ballot2, DrawLotsStrategy.RANDOM)

    result = ElectionRound.run(lot_inp)

    assert isinstance(result, DrawOfLots)
    assert result.wasDecidedByLot() is True

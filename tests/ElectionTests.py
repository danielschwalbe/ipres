import pytest
import numpy as np
import pandas as pd
from ipres import (
    Election, ElectionConfig, ConstituenciesConfig,
    Ballot, ElectionRound, ElectionRoundInput, Contestant
)

def make_simple_cc(size=1000):
    df = pd.DataFrame({
        'constituency_name': ["C1"],
        'constituency_size': [size],
    })
    return ConstituenciesConfig.from_dataframe(df)

def test_election_init():
    cc = make_simple_cc()
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"]
    )
    election = Election(electionConfig=config)
    assert election.electionConfig == config

from unittest.mock import MagicMock, patch

def test_election_run_flow_mocked():
    """Tests the loop in Election.run by mocking Ballot.run."""
    cc = make_simple_cc()
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"]
    )
    election = Election(electionConfig=config)

    # Mock Round 1: No winner, has next
    it1 = MagicMock(spec=Ballot)
    it1.hasWinner.return_value = False
    it1.hasNext.return_value = True
    next_input = MagicMock(spec=ElectionRoundInput)
    it1.getNextRoundInput.return_value = next_input

    # Mock Round 2: Winner A
    it2 = MagicMock(spec=Ballot)
    it2.hasWinner.return_value = True
    it2.getWinner.return_value = Contestant.from_party("A")

    with patch("ipres.election.Ballot.run") as mock_ballot_run, \
         patch("ipres.election.ElectionRound.run") as mock_round_run:
        mock_ballot_run.return_value = it1
        mock_round_run.return_value = it2

        iterations = []
        def callback(it):
            iterations.append(it)

        result = election.run(on_iteration_finished=callback)

        assert result == it2
        assert len(iterations) == 2
        assert iterations[0] == it1
        assert iterations[1] == it2
        mock_round_run.assert_called_with(next_input)

def test_election_run_lot_mocked():
    """Tests that lot decision is considered a round."""
    cc = make_simple_cc()
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )
    election = Election(electionConfig=config)

    it = MagicMock(spec=Ballot)
    it.hasWinner.side_effect = [False, True]
    it.getNextRoundInput.return_value = MagicMock()

    with patch("ipres.election.Ballot.run") as mock_ballot_run, \
         patch("ipres.election.ElectionRound.run") as mock_round_run:
        mock_ballot_run.return_value = it
        mock_round_run.return_value = it

        result = election.run()
        assert result == it
        assert mock_ballot_run.call_count >= 1

def test_election_run_initial_input_correct():
    """Verifies that Election.run creates the initial ElectionRoundInput correctly."""
    cc = make_simple_cc()
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )
    election = Election(electionConfig=config)

    it = MagicMock(spec=Ballot)
    it.hasWinner.return_value = True

    with patch("ipres.election.Ballot.run") as mock_run:
        mock_run.return_value = it
        election.run()

        args, kwargs = mock_run.call_args
        initial_input = args[0]
        assert isinstance(initial_input, ElectionRoundInput)
        assert initial_input.constituencies_config == cc
        assert set(initial_input.contestants.keys()) == {"A", "B"}
        assert initial_input.ballot_majority_percent == config.getBallotMajorityPercent()
        assert initial_input.previousRound is None
        assert isinstance(initial_input.rng, np.random.Generator)

def test_election_run_seeded_deterministic():
    """Verifies that providing a seed to ElectionConfig results in deterministic output."""
    cc = make_simple_cc(10_000)
    parties = ["A", "B", "C"]

    config1 = ElectionConfig(
        constituencies_config=cc,
        participating_parties=parties,
        seed=42
    )
    el1 = Election(config1)
    res1 = el1.run()
    votes1 = res1.getContestantsVotesAfterPossibleCoalitions()

    config2 = ElectionConfig(
        constituencies_config=cc,
        participating_parties=parties,
        seed=42
    )
    el2 = Election(config2)
    res2 = el2.run()
    votes2 = res2.getContestantsVotesAfterPossibleCoalitions()

    config3 = ElectionConfig(
        constituencies_config=cc,
        participating_parties=parties,
        seed=43
    )
    el3 = Election(config3)
    res3 = el3.run()
    votes3 = res3.getContestantsVotesAfterPossibleCoalitions()

    pd.testing.assert_series_equal(votes1, votes2)

    with pytest.raises(AssertionError):
        pd.testing.assert_series_equal(votes1, votes3)

def test_election_run_iterations_stored():
    cc = make_simple_cc(1000)
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"]
    )
    election = Election(electionConfig=config)

    iterations = []
    def callback(it):
        iterations.append(it)

    final_iteration = election.run(on_iteration_finished=callback)

    assert len(iterations) >= 1
    assert iterations[-1] == final_iteration
    assert final_iteration.hasWinner() or final_iteration.needsDecisionByLotInNextRound()

def test_election_run_callback():
    """Tests the on_iteration_finished callback."""
    cc = make_simple_cc()
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"]
    )
    election = Election(electionConfig=config)

    it = MagicMock(spec=Ballot)
    it.hasWinner.return_value = True

    called_its = []
    def callback(iteration):
        called_its.append(iteration)

    with patch("ipres.election.Ballot.run") as mock_run:
        mock_run.return_value = it
        election.run(on_iteration_finished=callback)

        assert len(called_its) == 1
        assert called_its[0] == it


# ---- start(votes=...) ----

def test_start_with_votes_injects_votes():
    """start(votes=...) must inject the given votes into the first round.

    Mutant #1384: with_votes call replaced by current_input = None → Ballot.run(None) crashes.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    ballot = election.start(votes={"A": 600, "B": 400})

    votes = ballot._vote_matrix.getVotes()
    assert int(votes.loc["C1", "A"]) == 600
    assert int(votes.loc["C1", "B"]) == 400


# ---- runNextIteration ----

def test_run_next_iteration_starts_when_no_prior_rounds():
    """runNextIteration on a fresh election starts the first round.

    Mutant #1385: == 0 → != 0 — empty election goes to else branch → None.getNextRoundInput() crashes.
    Mutant #1386: == 0 → == 1 — same crash (0 != 1 → else branch).
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    result = election.runNextIteration()

    assert isinstance(result, Ballot)
    assert election.getNumberOfIterations() == 1


def test_run_next_iteration_continues_from_last_round():
    """runNextIteration after a first round continues from that round's output.

    Mutant #1387: iterationInput is None → is not None — inverted None check uses None as input → crash.
    Mutant #1388: current_input = None → crash.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B", "C"])
    election = Election(electionConfig=config)

    ballot1 = election.start(votes={"A": 400, "B": 350, "C": 250})
    if ballot1.hasWinner():
        pytest.skip("First ballot unexpectedly produced a winner.")

    result = election.runNextIteration()

    assert isinstance(result, ElectionRound)
    assert election.getNumberOfIterations() == 2


# ---- iterations property ----

def test_iterations_property_returns_tuple():
    """election.iterations is a tuple, not a bound method.

    Mutant #1395: @property removed → attribute access returns the method object.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    assert isinstance(election.iterations, tuple)


# ---- getFirstIteration / getLastIteration ----

def test_get_first_iteration_returns_none_when_empty():
    """getFirstIteration returns None before any round has been run.

    Mutant #1397: > 0 → >= 0 — len([]) >= 0 is always True → IndexError on empty list.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    assert election.getFirstIteration() is None


def test_get_last_iteration_returns_none_when_empty():
    """getLastIteration returns None before any round has been run.

    Mutant #1401: > 0 → >= 0 — len([]) >= 0 is always True → IndexError on empty list.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    assert election.getLastIteration() is None


# ---- hadOutrightWinner ----

def test_had_outright_winner_raises_when_unfinished():
    """hadOutrightWinner raises Exception if the election has not concluded.

    Mutant #1414: XX-prefix on error message — anchored '^Election' match fails.
    """
    cc = make_simple_cc()
    config = ElectionConfig(constituencies_config=cc, participating_parties=["A", "B"])
    election = Election(electionConfig=config)

    with pytest.raises(Exception, match=r"^Election is not finished"):
        election.hadOutrightWinner()

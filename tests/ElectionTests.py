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

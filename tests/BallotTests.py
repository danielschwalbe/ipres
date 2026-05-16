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


# ---- ElectionRoundInput default round_number ----

def test_first_ballot_default_round_number_is_1():
    """First ballot without an explicit round_number gets getRoundNumber() == 1.

    ElectionRoundInput.round_number defaults to 0; the ballot increments it to 1.
    Mutant #179 sets the default to 1, making getRoundNumber() return 2.
    """
    cc = make_cc(1_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(
        cc, election, contestants,
        probabilities={"A": 60.0, "B": 40.0},
        turnout=100.0,
        ballot_majority_percent=55.0,
        rng=np.random.default_rng(0),
    )
    ballot = Ballot.run(_input)
    assert ballot.getRoundNumber() == 1


# ---- ElectionRoundInput.with_votes ----

def _make_two_constituency_cc() -> ConstituenciesConfig:
    df = pd.DataFrame({
        "constituency_name": ["WK1", "WK2"],
        "constituency_size": [1_000, 1_000],
    })
    return ConstituenciesConfig.from_dataframe(df)


def _make_round_input(cc, contestants) -> ElectionRoundInput:
    config = ElectionConfig(constituencies_config=cc, participating_parties=list(contestants.keys()), seed=0)
    election = Election(electionConfig=config)
    return ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestants,
        ballot_majority_percent=55.0,
    )


def test_with_votes_flat_dict_single_constituency():
    """with_votes(flat) for a single constituency sets the vote matrix correctly.

    Mutant #183: and→or causes flat dict to enter the nested-dict branch and fail.
    Mutant #186: != 1 → == 1 raises ValueError for valid single-constituency input.
    Mutant #190: df=None crashes when the VoteMatrix is constructed.
    """
    cc = make_cc(1_000)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = _make_round_input(cc, contestants)
    result = _input.with_votes({"A": 40, "B": 60})
    votes = result.vote_matrix.getVotes()
    assert int(votes.loc["C1", "A"]) == 40
    assert int(votes.loc["C1", "B"]) == 60


def test_with_votes_nested_dict_two_constituencies():
    """with_votes(nested) for multiple constituencies sets the vote matrix correctly.

    Mutant #182: constituency_names=None → AttributeError on reindex.
    Mutant #184: fillna(1) fills absent parties with 1 vote instead of 0.
    Mutant #185: df=None crashes on VoteMatrix construction.
    """
    cc = _make_two_constituency_cc()
    contestants = contestantsDictFromParties(["A", "B"])
    _input = _make_round_input(cc, contestants)
    result = _input.with_votes({"WK1": {"A": 30, "B": 20}, "WK2": {"A": 10, "B": 40}})
    votes = result.vote_matrix.getVotes()
    assert int(votes.loc["WK1", "A"]) == 30
    assert int(votes.loc["WK2", "B"]) == 40


def test_with_votes_flat_dict_raises_for_multiple_constituencies():
    """with_votes(flat) with multiple constituencies raises ValueError with the right message.

    Mutant #186: != 1 → == 1 — no error raised even though 2 constituencies are configured.
    Mutant #187: != 1 → != 2 — no error raised for exactly 2 constituencies.
    Mutant #161: XX-prefix on first string segment ("XXFlat votes dict ... constituency; XX").
    Mutant #162: XX-prefix on second string segment ("XXgot [...]. XX").
    The pattern "constituency; got" is present in the original but absent in both
    mutants 161 and 162 (which insert "XX" between "; " and "got").
    """
    cc = _make_two_constituency_cc()
    contestants = contestantsDictFromParties(["A", "B"])
    _input = _make_round_input(cc, contestants)
    with pytest.raises(ValueError, match="constituency; got"):
        _input.with_votes({"A": 30, "B": 20})


def test_with_votes_nested_dict_absent_party_gets_zero():
    """with_votes(nested) must fill absent party/constituency entries with 0, not 1.

    Mutant #157: fillna(0) → fillna(1) — absent B in WK1 would get 1 vote instead of 0.
    """
    cc = _make_two_constituency_cc()
    contestants = contestantsDictFromParties(["A", "B"])
    _input = _make_round_input(cc, contestants)
    result = _input.with_votes({"WK1": {"A": 30}, "WK2": {"A": 10, "B": 40}})
    votes = result.vote_matrix.getVotes()
    assert int(votes.loc["WK1", "B"]) == 0


# ---- Ballot.run: error message anchoring (mutant #606) ----

def test_ballot_run_requires_two_contestants_message():
    """Mutant #606: XX-prefix on error message — anchored match fails."""
    cc = make_cc()
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A"])
    _input = make_input(cc, election, contestants, ballot_majority_percent=55.0,
                        rng=np.random.default_rng(0))
    with pytest.raises(ValueError, match=r"^At least two contestants are required"):
        Ballot.run(_input)


# ---- round_number increment (mutant #620) ----

def test_ballot_round_number_increments_from_nonzero():
    """Mutant #620: round_number = 1 (not += 1) — starting from 5 gives 5 not 6."""
    cc = make_cc(1_000)
    election = make_election(cc)
    contestants = contestantsDictFromParties(["A", "B"])
    _input = make_input(cc, election, contestants,
                        probabilities={"A": 70.0, "B": 30.0},
                        turnout=100.0,
                        ballot_majority_percent=55.0,
                        rng=np.random.default_rng(0),
                        round_number=5)
    ballot = Ballot.run(_input)
    assert ballot.getRoundNumber() == 6


# ---- getContestantsByPercentageDesc ----

def _make_ballot_with_fixed_votes(votes_dict: dict, ballot_majority_percent: float = 55.0) -> Ballot:
    """Helper: create a Ballot with injected exact vote counts in a single constituency."""
    cc = make_cc(100_000)
    config = ElectionConfig(constituencies_config=cc,
                            participating_parties=list(votes_dict.keys()), seed=0)
    election = Election(electionConfig=config)
    contestants = contestantsDictFromParties(list(votes_dict.keys()))
    votes_df = pd.DataFrame(votes_dict, index=["C1"])
    pre_built = VoteMatrix.generate(cc, list(contestants.values()),
                                    vote_matrix=votes_df)
    _input = make_input(cc, election, contestants,
                        ballot_majority_percent=ballot_majority_percent,
                        vote_matrix=pre_built,
                        rng=np.random.default_rng(0))
    return Ballot.run(_input)


def test_get_contestants_by_percentage_desc_returns_series():
    """Mutant #649: pct = None instead of pct.round(decimals) — crashes on sort."""
    ballot = _make_ballot_with_fixed_votes({"A": 600, "B": 400})
    result = ballot.getContestantsByPercentageDesc(decimals=2)
    assert isinstance(result, pd.Series)
    assert abs(result.sum() - 100.0) < 0.1


def test_get_contestants_by_percentage_desc_threshold_zero_does_not_raise():
    """Mutant #654: threshold <= 0 raises for threshold=0 (valid lower bound)."""
    ballot = _make_ballot_with_fixed_votes({"A": 600, "B": 400})
    result = ballot.getContestantsByPercentageDesc(threshold=0)
    assert not result.empty


def test_get_contestants_by_percentage_desc_threshold_exact_boundary():
    """Mutant #661: csum > threshold (strict) excludes the party at exactly threshold.

    B=65%, A=35%. With threshold=65: cumsum at B=65% equals 65 exactly.
    Original (>=): mask True at B → return [B] only.
    Mutant (>): 65 > 65 = False → continue to A → return [B, A].
    """
    ballot = _make_ballot_with_fixed_votes({"A": 350, "B": 650}, ballot_majority_percent=70.0)
    result = ballot.getContestantsByPercentageDesc(threshold=65.0)
    assert len(result) == 1
    assert result.index[0] == "B"


def test_get_contestants_by_percentage_desc_zero_total():
    """Mutant #640: total < 0 instead of <= 0 — zero total triggers divide-by-zero.
    Mutants #689-692: same zero-total edge case in show_results_table.

    Inject a vote matrix of all zeros and verify no crash + all-zero percentages.
    """
    cc = make_cc(100_000)
    config = ElectionConfig(constituencies_config=cc,
                            participating_parties=["A", "B"], seed=0)
    election = Election(electionConfig=config)
    contestants = contestantsDictFromParties(["A", "B"])
    votes_df = pd.DataFrame({"A": [0], "B": [0]}, index=["C1"])
    pre_built = VoteMatrix.generate(cc, list(contestants.values()), vote_matrix=votes_df)
    _input = make_input(cc, election, contestants,
                        ballot_majority_percent=55.0,
                        vote_matrix=pre_built,
                        rng=np.random.default_rng(0))
    ballot = Ballot.run(_input)
    result = ballot.getContestantsByPercentageDesc()
    assert (result == 0.0).all()
    table = ballot.show_results_table()
    pct_col = table.columns[1]
    assert (table[pct_col] == 0.0).all()


# ---- show_results_table (mutants #683, #693-695, #706) ----

def test_show_results_table_returns_dataframe_with_correct_percentages():
    """Mutants #683 (styler=True default → returns Styler), #693-695 (wrong % calc),
    #706 (invalid sort kind crashes).

    With A=600, B=400: A=60%, B=40%. Sum=100%.
    """
    ballot = _make_ballot_with_fixed_votes({"A": 600, "B": 400})
    result = ballot.show_results_table()
    assert isinstance(result, pd.DataFrame)
    pct_col = result.columns[1]
    assert abs(result[pct_col].sum() - 100.0) < 0.5


# ---- formCoalition error messages ----

def test_form_coalition_unknown_contestant_message():
    """Mutant #671: XX-prefix on 'Not among the contestants' error message.

    Must pass Contestant objects (not strings): string lookup raises KeyError before
    the 'extra' validation. Passing a Contestant object that is not in this round
    triggers the intended ValueError.
    """
    ballot = _make_ballot_with_fixed_votes({"A": 400, "B": 350, "C": 250},
                                           ballot_majority_percent=60.0)
    if ballot.hasWinner():
        pytest.skip("Unexpected winner; adjust vote counts.")
    a = ballot._contestants["A"]
    outsider = Contestant.from_party("X")
    with pytest.raises(ValueError, match=r"^Not among the contestants"):
        ballot.formCoalition("AX", [a, outsider])


def test_form_coalition_all_message():
    """Mutant #677: XX-prefix on 'At least two contestants must compete' message."""
    ballot = _make_ballot_with_fixed_votes({"A": 400, "B": 350, "C": 250},
                                           ballot_majority_percent=60.0)
    if ballot.hasWinner():
        pytest.skip("Unexpected winner; adjust vote counts.")
    with pytest.raises(ValueError, match=r"^At least two contestants must compete"):
        ballot.formCoalition("ALL", ["A", "B", "C"])


def test_form_coalition_single_element_list():
    """Mutant #666: contestants[1] instead of contestants[0] — IndexError for 1-element list."""
    ballot = _make_ballot_with_fixed_votes({"A": 400, "B": 350, "C": 250},
                                           ballot_majority_percent=60.0)
    if ballot.hasWinner():
        pytest.skip("Unexpected winner; adjust vote counts.")
    ballot.formCoalition("A_solo", ["A"])
    assert "A_solo" in ballot.getContestants()


# ---- _evaluateResult: winner at exact threshold (mutant #748) ----

def test_ballot_winner_at_exact_majority_threshold():
    """Mutant #748: >= getBallotMajorityPercent() → > — winner at exact threshold not detected.

    With A=550, B=450 (A=55.0%) and ballot_majority_percent=55.0: A should win outright.
    Mutant makes the condition strict (>), so A at exactly 55.0% is NOT considered a winner.
    """
    ballot = _make_ballot_with_fixed_votes({"A": 550, "B": 450}, ballot_majority_percent=55.0)
    assert ballot.hasWinner()
    assert ballot.getWinner().name == "A"


# ---- _calculate_member_vote_weights: zero total (mutants #770-772) ----

def test_calculate_member_vote_weights_zero_total():
    """Mutants #770 (2/len), #771 (1*len), #772 (None) — wrong weights when all votes=0.

    When a coalition's members all have 0 votes, equal weights (1/n) should be assigned.
    With 2 members, each gets 0.5. Mutants give 1.0, 2.0, or None.
    """
    ballot = _make_ballot_with_fixed_votes({"A": 0, "B": 0, "C": 0},
                                           ballot_majority_percent=60.0)
    contestants_list = [ballot._contestants["A"], ballot._contestants["B"]]
    weights = ballot._calculate_member_vote_weights(contestants_list)
    assert abs(weights["A"] - 0.5) < 1e-9
    assert abs(weights["B"] - 0.5) < 1e-9
    assert abs(sum(weights.values()) - 1.0) < 1e-9

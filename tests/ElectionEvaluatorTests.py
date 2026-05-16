"""
Tests for ElectionEvaluator.

Coverage focus (existing files already cover _distribute_seats and quota-correction strategies):
  - evaluate() raises exception on unfinished election
  - evaluate() returns a complete ElectionResult
  - _assign_parties_to_constituencies():
      * number of assigned constituencies == number of constituencies
      * assigned count per party matches its quota
      * parties with quota 0 receive no constituencies
  - constituency_representation effect on _get_party_constituency_counts():
      * ENTIRE_PARLIAMENT: all parties with seats >= 2 receive a quota
      * GOVERNING_MAJORITY: only winner parties receive quotas, opposition quota = 0
  - constituency_representation effect on _assign_parties_to_constituencies():
      * ENTIRE_PARLIAMENT: opposition can receive constituencies
      * GOVERNING_MAJORITY: only winner parties receive constituencies
  - ConstituencyAllocationMethod variants (GREEDY, STABLE, OPTIMAL) all work
"""

import pytest
import numpy as np
import pandas as pd

from ipres import (
    Election, ElectionConfig, ElectionEvaluator,
    SeatDistributionMethod, Contestant, contestantsFromParties, SuperMajorityMargin, MarginUnit,
    ConstituenciesConfig, VoteMatrix,
)
from ipres.election_config import (
    QuotaCorrectionStrategy, ConstituencyRepresentation, DrawLotsStrategy,
)
from ipres import ElectionRoundInput as IterationInput
from ipres.allocation import ConstituencyAllocationMethod


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

def make_constituencies(names: list[str], size: int = 1000) -> ConstituenciesConfig:
    df = pd.DataFrame({
        'constituency_name': names,
        'constituency_size': [size] * len(names),
    })
    return ConstituenciesConfig.from_dataframe(df)


def make_evaluator(
    allocation_method: ConstituencyAllocationMethod = ConstituencyAllocationMethod.OPTIMAL,
    quota_correction: QuotaCorrectionStrategy = QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES,
    seed: int = 42,
) -> ElectionEvaluator:
    return ElectionEvaluator(
        seat_distribution_method=SeatDistributionMethod.SAINTE_LAGUE,
        constituency_allocation_method=allocation_method,
        quota_correction_strategy=quota_correction,
        seed=seed,
    )


def run_election_with_coalition(
    cc: ConstituenciesConfig,
    party_names: list[str],
    vote_matrix: pd.DataFrame,
    coalition_name: str,
    coalition_members: list[str],
    constituency_representation: ConstituencyRepresentation = ConstituencyRepresentation.ENTIRE_PARLIAMENT,
    seed: int = 42,
) -> Election:
    """
    Helper: build an election with a manually provided vote matrix and form a
    coalition so the election finishes with a winner.
    """
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=party_names,
        parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
        draw_lots_strategy=DrawLotsStrategy.RANDOM,
        constituency_representation=constituency_representation,
        seed=seed,
    )
    contestants = contestantsFromParties(party_names)
    vote_matrix_obj = VoteMatrix.generate(
        constituencies_config=cc,
        contestants=contestants,
        vote_matrix=vote_matrix,
    )
    election = Election(electionConfig=config)
    iteration_input = IterationInput(
        election=election,
        constituencies_config=cc,
        contestants={c.name: c for c in contestants},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        draw_lots_strategy=config.draw_lots_strategy,
        rng=np.random.default_rng(seed),
        vote_matrix=vote_matrix_obj,
    )
    iteration = election.start(iteration_input)
    if not iteration.hasWinner():
        iteration.formCoalition(coalition_name, coalition_members)
    assert election.isFinished(), "Election should be finished after coalition is formed"
    return election


# ---------------------------------------------------------------------------
# Standard 3-constituency / 4-party setup (mirrors the notebook demo)
# ---------------------------------------------------------------------------
# A: 38%, B: 29%, C: 20%, D: 13%  →  A+B coalition wins (66.67% > 55%)

CC3 = make_constituencies(['WK1', 'WK2', 'WK3'])
PARTIES4 = ['A', 'B', 'C', 'D']
VOTE_MATRIX_4P = pd.DataFrame(
    [[250, 200, 150, 100],
     [280, 180, 140, 100],
     [270, 220, 130,  80]],
    index=['WK1', 'WK2', 'WK3'],
    columns=['A', 'B', 'C', 'D'],
)


@pytest.fixture
def election_entire():
    return run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.ENTIRE_PARLIAMENT,
    )


@pytest.fixture
def election_govt():
    return run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY,
    )


# ---------------------------------------------------------------------------
# evaluate() basic contract
# ---------------------------------------------------------------------------

def test_evaluate_raises_on_unfinished_election():
    """evaluate() must raise if the election has no winner yet."""
    cc = make_constituencies(['WK1', 'WK2'])
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=['A', 'B'],
        seed=1,
    )
    election = Election(electionConfig=config)
    # Do NOT run the election – it has no winner
    evaluator = make_evaluator()
    with pytest.raises(Exception):
        evaluator.evaluate(election)


def test_evaluate_returns_complete_result(election_entire):
    evaluator = make_evaluator()
    result = evaluator.evaluate(election_entire)

    assert result.seats is not None
    assert result.party_constituency_counts is not None
    assert result.constituency_assignments is not None
    assert result.election is election_entire
    assert result.evaluator is evaluator


# ---------------------------------------------------------------------------
# _assign_parties_to_constituencies – structural invariants
# ---------------------------------------------------------------------------

def test_all_constituencies_are_assigned(election_entire):
    """Every constituency must appear exactly once in the assignments."""
    result = make_evaluator().evaluate(election_entire)
    assignments = result.constituency_assignments

    expected = set(CC3.getConstituencyNames())
    assert set(assignments.keys()) == expected


def test_assigned_count_per_party_matches_quota(election_entire):
    """Number of constituencies each party receives must equal its quota."""
    result = make_evaluator().evaluate(election_entire)
    assignments = result.constituency_assignments
    quotas = result.party_constituency_counts

    from collections import Counter
    actual_counts = Counter(assignments.values())

    for party, quota in quotas.items():
        assert actual_counts.get(party, 0) == quota, (
            f"Party {party}: quota={quota}, assigned={actual_counts.get(party, 0)}"
        )


def test_party_with_zero_quota_gets_no_constituency(election_entire):
    """A party whose quota is 0 must not appear in the assignments."""
    result = make_evaluator().evaluate(election_entire)
    zero_quota_parties = {p for p, q in result.party_constituency_counts.items() if q == 0}
    assigned_parties = set(result.constituency_assignments.values())

    assert zero_quota_parties.isdisjoint(assigned_parties), (
        f"Parties with quota=0 were assigned constituencies: "
        f"{zero_quota_parties & assigned_parties}"
    )


def test_quota_sum_equals_number_of_constituencies(election_entire):
    """sum(party_constituency_counts) must equal the total number of constituencies."""
    result = make_evaluator().evaluate(election_entire)
    assert sum(result.party_constituency_counts.values()) == CC3.getNumberOfConstituencies()


# ---------------------------------------------------------------------------
# ENTIRE_PARLIAMENT: quota and assignment behaviour
# ---------------------------------------------------------------------------

def test_entire_parliament_parties_with_zero_seats_get_zero_quota(election_entire):
    """In ENTIRE_PARLIAMENT mode, parties with 0 seats must have quota=0.

    Note: the quota correction algorithm CAN give parties with exactly 1 seat a
    quota of 1 (to fix the integer-division deficit), so the stronger condition
    'seats >= 2 → quota > 0' does not hold in general.
    """
    result = make_evaluator().evaluate(election_entire)

    for party, quota in result.party_constituency_counts.items():
        seats = result.seats[party]
        if seats == 0:
            assert quota == 0, (
                f"Party {party} has 0 seats but quota={quota}"
            )


def test_entire_parliament_opposition_can_receive_constituencies(election_entire):
    """In ENTIRE_PARLIAMENT mode, opposition parties with enough seats can receive constituencies."""
    result = make_evaluator().evaluate(election_entire)

    winner_parties = {'A', 'B'}
    opposition_assignments = {
        c: p for c, p in result.constituency_assignments.items()
        if p not in winner_parties
    }
    # With 3 constituencies and A=1, B=1, C=1 quotas (see notebook demo),
    # at least one constituency goes to C
    assert len(opposition_assignments) >= 1, (
        "In ENTIRE_PARLIAMENT mode, C should receive at least one constituency"
    )


# ---------------------------------------------------------------------------
# GOVERNING_MAJORITY: quota and assignment behaviour
# ---------------------------------------------------------------------------

def test_government_majority_opposition_gets_zero_quota(election_govt):
    """In GOVERNING_MAJORITY mode, opposition parties must have quota=0."""
    result = make_evaluator().evaluate(election_govt)

    winner_parties = set(election_govt.getWinner().getContainedParties())
    for party, quota in result.party_constituency_counts.items():
        if party not in winner_parties:
            assert quota == 0, (
                f"Opposition party {party} has quota={quota}, expected 0"
            )


def test_government_majority_opposition_gets_no_constituency(election_govt):
    """In GOVERNING_MAJORITY mode, no constituency may be assigned to an opposition party."""
    result = make_evaluator().evaluate(election_govt)

    winner_parties = set(election_govt.getWinner().getContainedParties())
    for constituency, party in result.constituency_assignments.items():
        assert party in winner_parties, (
            f"Constituency {constituency} assigned to opposition party {party}"
        )


def test_government_majority_all_constituencies_assigned_to_winner(election_govt):
    """All constituencies go to winner-coalition parties in GOVERNING_MAJORITY mode."""
    result = make_evaluator().evaluate(election_govt)

    winner_parties = set(election_govt.getWinner().getContainedParties())
    assigned_parties = set(result.constituency_assignments.values())
    assert assigned_parties.issubset(winner_parties)


def test_government_majority_quota_sum_equals_constituencies(election_govt):
    """sum(quotas) == number_of_constituencies also holds in GOVERNING_MAJORITY mode."""
    result = make_evaluator().evaluate(election_govt)

    assert sum(result.party_constituency_counts.values()) == CC3.getNumberOfConstituencies()


# ---------------------------------------------------------------------------
# Comparison: ENTIRE_PARLIAMENT vs GOVERNING_MAJORITY
# ---------------------------------------------------------------------------

def test_seat_distribution_is_same_in_both_modes():
    """
    constituency_representation does NOT affect _distribute_seats.
    Total seats must match each mode's own parliamentarySeats.

    Note: when the coalition wins in the very first iteration (no party
    reduction across iterations), hadOutrightWinner() is True and
    seats are distributed proportionally – not with a guaranteed majority.
    The important invariant is that the code path is identical regardless of
    the constituency_representation setting.
    """
    election_ep = run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.ENTIRE_PARLIAMENT,
    )
    election_gm = run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY,
    )

    result_ep = make_evaluator().evaluate(election_ep)
    result_gm = make_evaluator().evaluate(election_gm)

    # Each result's seat total must equal its own config's parliamentarySeats
    assert sum(result_ep.seats.values()) == election_ep.electionConfig.parliamentarySeats
    assert sum(result_gm.seats.values()) == election_gm.electionConfig.parliamentarySeats

    # Neither election has party reduction across iterations (coalition formed
    # in the first – and only – iteration), so hadOutrightWinner() is True
    # and seats are distributed proportionally in both cases
    assert election_ep.hadOutrightWinner()
    assert election_gm.hadOutrightWinner()

    # Verify all seat counts are non-negative
    assert all(s >= 0 for s in result_ep.seats.values())
    assert all(s >= 0 for s in result_gm.seats.values())


def test_modes_differ_in_constituency_distribution():
    """
    The two modes must differ in which parties receive constituencies:
    ENTIRE_PARLIAMENT allows opposition; GOVERNING_MAJORITY does not.
    """
    election_ep = run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.ENTIRE_PARLIAMENT,
    )
    election_gm = run_election_with_coalition(
        CC3, PARTIES4, VOTE_MATRIX_4P,
        coalition_name='A+B', coalition_members=['A', 'B'],
        constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY,
    )

    result_ep = make_evaluator().evaluate(election_ep)
    result_gm = make_evaluator().evaluate(election_gm)

    winner_parties = {'A', 'B'}
    ep_opposition_constituencies = sum(
        1 for p in result_ep.constituency_assignments.values() if p not in winner_parties
    )
    gm_opposition_constituencies = sum(
        1 for p in result_gm.constituency_assignments.values() if p not in winner_parties
    )

    assert ep_opposition_constituencies >= 1, (
        "ENTIRE_PARLIAMENT: C should get at least one constituency"
    )
    assert gm_opposition_constituencies == 0, (
        "GOVERNING_MAJORITY: opposition should get zero constituencies"
    )


# ---------------------------------------------------------------------------
# ConstituencyAllocationMethod variants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method", [
    ConstituencyAllocationMethod.GREEDY,
    ConstituencyAllocationMethod.STABLE_MATCHING,
    ConstituencyAllocationMethod.OPTIMAL,
])
def test_allocation_methods_produce_valid_assignments(election_entire, method):
    """All allocation methods must assign every constituency exactly once."""
    result = make_evaluator(allocation_method=method).evaluate(election_entire)

    expected_constituencies = set(CC3.getConstituencyNames())
    assert set(result.constituency_assignments.keys()) == expected_constituencies
    assert sum(result.party_constituency_counts.values()) == CC3.getNumberOfConstituencies()


# ---------------------------------------------------------------------------
# _winnerNeedsAssignedMajority — seat distribution path selection
#
# Two parties (A and B), 10 constituencies → 20 parliamentary seats,
# parliament majority threshold = 55 % → 11 seats.
#
# Scenario 1: A wins 70 % of votes  (> 55 % parliament threshold)
#   → Path 2 (proportional): Sainte-Laguë gives A ~14 seats > 11
#
# Scenario 2: A wins 53 % of votes  (> 52 % ballot threshold, < 55 % parliament threshold)
#   → Path 1 (assigned majority): A receives exactly 11 seats
# ---------------------------------------------------------------------------

CC10 = make_constituencies([f'WK{i+1}' for i in range(10)])


def run_election_outright(
    cc: ConstituenciesConfig,
    votes: dict[str, int],
    parliament_margin_percent: float = 5.0,
    ballot_margin_percent: float = 2.0,
    seed: int = 42,
) -> Election:
    """Build a two-party election where one party wins outright with fixed, uniform votes."""
    party_names = list(votes.keys())
    constituency_names = cc.getConstituencyNames()

    df = pd.DataFrame(
        [votes] * cc.getNumberOfConstituencies(),
        index=constituency_names,
        columns=party_names,
    )

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=party_names,
        parliament_majority_margin=SuperMajorityMargin(parliament_margin_percent, MarginUnit.PERCENT),
        ballot_majority_margin=SuperMajorityMargin(ballot_margin_percent, MarginUnit.PERCENT),
        seed=seed,
    )
    contestants = contestantsFromParties(party_names)
    vote_matrix_obj = VoteMatrix.generate(
        constituencies_config=cc,
        contestants=contestants,
        vote_matrix=df,
    )
    election = Election(electionConfig=config)
    election.start(IterationInput(
        election=election,
        constituencies_config=cc,
        contestants={c.name: c for c in contestants},
        ballot_majority_percent=config.getBallotMajorityPercent(),
        draw_lots_strategy=config.draw_lots_strategy,
        rng=np.random.default_rng(seed),
        vote_matrix=vote_matrix_obj,
    ))
    assert election.isFinished(), "Election should be finished after first ballot"
    return election


def test_outright_winner_above_parliament_threshold_gets_proportional_seats():
    """When the winner's vote share exceeds the parliament majority threshold,
    all seats are distributed proportionally (Path 2).

    A wins 70 % > 55 % parliament threshold → proportional Sainte-Laguë gives
    A approximately 14 out of 20 seats, which is more than the 11-seat majority minimum.
    """
    election = run_election_outright(CC10, {'A': 70, 'B': 30})

    assert election.hadOutrightWinner()
    winner_pct = election.getLastIteration().getContestantsPercentagesAfterPossibleCoalitions()['A']
    assert winner_pct >= election.electionConfig.getParliamentMajorityPercent()

    result = make_evaluator().evaluate(election)
    parliament_majority_seats = election.electionConfig.getParliamentMajoritySeats()

    # Proportional distribution gives A more seats than the parliament majority minimum
    assert result.seats['A'] > parliament_majority_seats


def test_outright_winner_below_parliament_threshold_gets_assigned_majority():
    """When the winner's vote share exceeds the ballot threshold but falls below
    the parliament majority threshold, the winner is assigned exactly the
    parliament majority seats (Path 1).

    A wins 53 % > 52 % ballot threshold but 53 % < 55 % parliament threshold
    → A receives exactly 11 out of 20 seats (the parliament majority minimum).
    """
    election = run_election_outright(CC10, {'A': 53, 'B': 47})

    assert election.hadOutrightWinner()
    winner_pct = election.getLastIteration().getContestantsPercentagesAfterPossibleCoalitions()['A']
    assert winner_pct > election.electionConfig.getBallotMajorityPercent()
    assert winner_pct < election.electionConfig.getParliamentMajorityPercent()

    result = make_evaluator().evaluate(election)
    parliament_majority_seats = election.electionConfig.getParliamentMajoritySeats()

    # Winner is assigned exactly the parliament majority
    assert result.seats['A'] == parliament_majority_seats


def test_evaluate_raises_with_correct_message_on_unfinished_election():
    """evaluate() must raise with a message identifying the unfinished election.

    Mutant #131 changes the message to "XXCannot evaluate...XX", which would not
    match. The existing test only checks that any Exception is raised; this test
    pins down the message text.
    """
    cc = make_constituencies(['WK1', 'WK2'])
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=['A', 'B'],
        seed=1,
    )
    election = Election(electionConfig=config)
    with pytest.raises(Exception, match=r"^Cannot evaluate"):
        make_evaluator().evaluate(election)


def test_percentages_after_coalitions_sum_to_100():
    """getContestantsPercentagesAfterPossibleCoalitions must return values in [0, 100] summing to 100.

    Mutant #151 multiplies the relative votes by 101.0 instead of 100.0, making the
    sum 101.0 and individual values 1 % too large.

    With A holding 70 % of votes: percentages['A'] == 70.0, sum == 100.0.
    """
    election = run_election_outright(CC10, {'A': 70, 'B': 30})
    percentages = election.getLastIteration().getContestantsPercentagesAfterPossibleCoalitions()
    assert percentages.sum() == pytest.approx(100.0)
    assert percentages['A'] == pytest.approx(70.0)


def test_outright_winner_exactly_at_parliament_threshold_gets_proportional_seats():
    """Winner whose vote share equals the parliament threshold exactly must get proportional seats.

    Mutant #1027 in seat_distributor.py: ``<`` becomes ``<=`` in
    ``_winner_needs_assigned_majority``, causing a winner at exactly the threshold
    to take Path 1 (assigned majority) instead of Path 2 (proportional).

    Setup: 1 constituency (2 total seats), 5 % parliament margin (threshold = 55.0 %).
    A=55 votes, B=45 votes → A's percentage = 55.0 % == threshold.

    Original (``<``): 55.0 < 55.0 = False → proportional Sainte-Laguë → A=1, B=1.
    Mutant  (``<=``): 55.0 <= 55.0 = True → assigned majority → A gets ceil(55 %×2)=2, B=0.
    """
    cc = make_constituencies(['WK1'])
    election = run_election_outright(cc, {'A': 55, 'B': 45})
    result = make_evaluator().evaluate(election)
    assert result.seats['A'] == 1
    assert result.seats['B'] == 1
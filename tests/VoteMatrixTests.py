import math
import warnings

import numpy as np
import pandas as pd
import pytest

from ipres import VoteMatrix, ConstituenciesConfig, Contestant, contestantsFromParties, VoteMatrixAnalyzer
from ipres.contestant import Contestant as ContestantDirect


def make_constituencies(names: list[str], sizes: list[int]) -> ConstituenciesConfig:
    df = pd.DataFrame({
        'constituency_name': names,
        'constituency_size': sizes,
    })
    return ConstituenciesConfig.from_dataframe(df)


def make_parties(names: list[str]) -> list[Contestant]:
    return contestantsFromParties(names)


def test_run_with_mapping_probabilities_and_turnout():
    # Given
    cc = make_constituencies(["C1", "C2", "C3"], [1000, 500, 200])
    parties = make_parties(["A", "B", "C"])  # N = 3
    probs_pct = {"A": 50.0, "B": 30.0, "C": 20.0}
    turnout_pct = {"C1": 80.0, "C2": 50.0, "C3": 0.0}  # last one produces a zero row
    rng = np.random.default_rng(12345)

    # When
    ballot = VoteMatrix.generate(cc, parties, probabilities=probs_pct, rng=rng, turnout=turnout_pct)

    # Then
    df = ballot.getVotes()
    assert list(df.index) == ["C1", "C2", "C3"]
    assert list(df.columns) == ["A", "B", "C"]

    # Row totals equal rounded(size * turnout)
    expected_sizes = np.round(np.array([1000, 500, 200]) * np.array([0.8, 0.5, 0.0])).astype(int)
    row_totals = df.sum(axis=1).to_numpy()
    assert np.array_equal(row_totals, expected_sizes)

    # Third row is all zeros due to 0% turnout
    assert (df.loc["C3"].to_numpy() == np.array([0, 0, 0])).all()


def test_probabilities_sequence_length_validation():
    cc = make_constituencies(["X"], [1000])
    parties = make_parties(["A", "B", "C"])  # N = 3
    rng = np.random.default_rng(1)
    # Wrong length
    try:
        VoteMatrix.generate(cc, parties, probabilities=[50.0, 50.0], rng=rng, turnout=80.0)
        assert False, "Expected ValueError for wrong length sequence"
    except ValueError as e:
        assert "Länge" in str(e) or "length" in str(e)


def test_turnout_sequence_length_validation():
    cc = make_constituencies(["X", "Y"], [100, 200])
    parties = make_parties(["A"])  # N = 1
    rng = np.random.default_rng(2)
    # Wrong length
    try:
        VoteMatrix.generate(cc, parties, probabilities=[100.0], rng=rng, turnout=[50.0])
        assert False, "Expected ValueError for wrong turnout sequence length"
    except ValueError as e:
        assert "Länge" in str(e) or "length" in str(e)


def test_missing_keys_in_mappings_raise():
    cc = make_constituencies(["A1"], [100])
    parties = make_parties(["A", "B"])  # expect keys for both
    rng = np.random.default_rng(3)

    # Missing probability for B
    try:
        VoteMatrix.generate(cc, parties, probabilities={"A": 100.0}, rng=rng, turnout=90.0)
        assert False, "Expected ValueError for missing probability key"
    except ValueError as e:
        assert "Missing probability" in str(e)

    # Missing turnout for constituency
    try:
        VoteMatrix.generate(cc, parties, probabilities={"A": 60.0, "B": 40.0}, rng=rng, turnout={})
        assert False, "Expected ValueError for missing turnout key"
    except ValueError as e:
        assert "Missing turnout" in str(e)


def test_getContestantsByPercentDesc_and_threshold():
    # Use big sizes to reduce sampling noise
    cc = make_constituencies(["C1", "C2"], [100_000, 200_000])
    parties = make_parties(["A", "B", "C"])  # N = 3
    probs_pct = {"A": 50.0, "B": 30.0, "C": 20.0}
    rng = np.random.default_rng(777)

    ballot = VoteMatrix.generate(cc, parties, probabilities=probs_pct, rng=rng, turnout=100.0)

    pct = ballot.getContestantsByPercentDesc(decimals=2)
    assert math.isclose(float(pct.sum()), 100.0, abs_tol=0.01)
    # non-increasing order
    assert all(pct.iloc[i] >= pct.iloc[i + 1] - 1e-9 for i in range(len(pct) - 1))
    assert list(pct.index) == ["A", "B", "C"]

    # Threshold e.g., 60% should include A and B but not C
    top = ballot.getContestantsByPercentThreshold(60.0, decimals=2)
    assert list(top.index)[:2] == ["A", "B"]
    assert top.sum() >= 60.0


def test_show_votes_table_percent_rowwise_and_zero_handling():
    cc = make_constituencies(["C1", "C2"], [1000, 500])
    parties = make_parties(["A", "B"])  # N = 2
    probs_pct = [70.0, 30.0]
    turnout_pct = [100.0, 0.0]  # second constituency has no votes
    rng = np.random.default_rng(9)

    ballot = VoteMatrix.generate(cc, parties, probabilities=probs_pct, rng=rng, turnout=turnout_pct)
    pct_df = ballot.show_votes_table_percent(styler=False, decimals=2)

    # Row 1 sums to ~100 (with rounding tolerance)
    assert math.isclose(float(pct_df.iloc[0].sum()), 100.0, abs_tol=0.05)
    # Row 2 all zeros
    assert (pct_df.iloc[1].to_numpy() == np.array([0.0, 0.0])).all()

    # styler flag returns a Styler
    styler = ballot.show_votes_table_percent(styler=True, decimals=1)
    from pandas.io.formats.style import Styler
    assert isinstance(styler, Styler)


def test_probabilities_out_of_bounds():
    cc = make_constituencies(["C"], [100])
    parties = make_parties(["A", "B"])  # N = 2
    rng = np.random.default_rng(5)

    # Negative probability
    try:
        VoteMatrix.generate(cc, parties, probabilities=[-1.0, 101.0], rng=rng, turnout=100.0)
        assert False, "Expected ValueError for negative prob"
    except ValueError:
        pass

    # Over 100 probability
    try:
        VoteMatrix.generate(cc, parties, probabilities=[50.0, 120.0], rng=rng, turnout=100.0)
        assert False, "Expected ValueError for >100 prob"
    except ValueError:
        pass


def test_probabilities_normalization_warning_when_not_sum_100():
    cc = make_constituencies(["C"], [10_000])
    parties = make_parties(["A", "B"])  # N = 2
    rng = np.random.default_rng(12)

    # Sum to 80 -> expect warning and auto-normalization
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ballot = VoteMatrix.generate(cc, parties, probabilities=[60.0, 20.0], rng=rng, turnout=100.0)
        # There should be at least one warning about normalization
        assert any("Auto-normalizing" in str(x.message) for x in w)

    # After normalization, the dominant party should still have > 70% of votes (roughly)
    pct = ballot.getContestantsByPercentDesc(decimals=0)
    assert pct.iloc[0] > 70.0


def test_getRelativeVoteMatrix():
    # Given: 3 constituencies with known vote distributions
    cc = make_constituencies(["C1", "C2", "C3"], [1000, 1000, 1000])
    parties = make_parties(["A", "B", "C"])
    # Use fixed seed for reproducibility
    rng = np.random.default_rng(42)
    probs_pct = {"A": 50.0, "B": 30.0, "C": 20.0}

    # When
    ballot = VoteMatrix.generate(cc, parties, probabilities=probs_pct, rng=rng, turnout=100.0)
    ballot_evaluator = VoteMatrixAnalyzer(ballot.getVotes())
    relative_matrix = ballot_evaluator.getRelativeVoteMatrix()

    # Then
    # 1. Check shape: same as votes matrix
    assert relative_matrix.shape == ballot.getVotes().shape
    assert list(relative_matrix.index) == ["C1", "C2", "C3"]
    assert list(relative_matrix.columns) == ["A", "B", "C"]

    # 2. Each row should sum to 1.0 (or very close due to floating point)
    row_sums = relative_matrix.sum(axis=1)
    for constituency in relative_matrix.index:
        assert math.isclose(row_sums[constituency], 1.0, abs_tol=1e-10), \
            f"Row {constituency} sum is {row_sums[constituency]}, expected 1.0"

    # 3. All values should be between 0 and 1
    assert (relative_matrix >= 0).all().all()
    assert (relative_matrix <= 1).all().all()


def test_getRelativeVoteMatrix_with_zero_turnout():
    # Given: One constituency with zero turnout
    cc = make_constituencies(["C1", "C2"], [1000, 1000])
    parties = make_parties(["A", "B"])
    rng = np.random.default_rng(123)
    turnout_pct = {"C1": 100.0, "C2": 0.0}  # C2 has no votes

    # When
    ballot = VoteMatrix.generate(cc, parties, probabilities=[60.0, 40.0], rng=rng, turnout=turnout_pct)
    ballot_evaluator = VoteMatrixAnalyzer(ballot.getVotes())
    relative_matrix = ballot_evaluator.getRelativeVoteMatrix()

    # Then
    # C1 should sum to 1.0
    assert math.isclose(relative_matrix.loc["C1"].sum(), 1.0, abs_tol=1e-10)

    # C2 should be all zeros (no division by zero error)
    assert (relative_matrix.loc["C2"].to_numpy() == np.array([0.0, 0.0])).all()


def test_getConstituencyImportanceMatrix():
    # Given: Simple scenario with 3 constituencies and 2 parties
    cc = make_constituencies(["C1", "C2", "C3"], [1000, 1000, 1000])
    parties = make_parties(["A", "B"])
    rng = np.random.default_rng(777)
    probs_pct = {"A": 60.0, "B": 40.0}

    # When
    ballot = VoteMatrix.generate(cc, parties, probabilities=probs_pct, rng=rng, turnout=100.0)
    ballot_evaluator = VoteMatrixAnalyzer(ballot.getVotes())
    importance_matrix = ballot_evaluator.getConstituencyImportanceMatrix()

    # Then
    # 1. Check shape
    assert importance_matrix.shape == ballot.getVotes().shape
    assert list(importance_matrix.index) == ["C1", "C2", "C3"]
    assert list(importance_matrix.columns) == ["A", "B"]

    # 2. All values should be non-negative
    assert (importance_matrix >= 0).all().all()

    # 3. For each party, the importance values should make sense
    # The formula is: w_ij = (M-1) *r_ij / sum(r_kj for k != i)
    relative_votes = ballot_evaluator.getRelativeVoteMatrix()
    M = relative_votes.shape[0]

    for party in importance_matrix.columns:
        total_share = relative_votes[party].sum()
        for constituency in importance_matrix.index:
            r_ij = relative_votes.loc[constituency, party]
            expected_denominator = total_share - r_ij

            if expected_denominator > 0:
                expected_importance = (M-1) * r_ij / expected_denominator
                actual_importance = importance_matrix.loc[constituency, party]
                assert math.isclose(actual_importance, expected_importance, abs_tol=1e-10), \
                    f"Importance for {constituency}, {party} mismatch"
            else:
                # Should be 0 if party only has votes in this constituency
                assert importance_matrix.loc[constituency, party] == 0.0


def test_getConstituencyImportanceMatrix_single_constituency_scenario():
    # Given: Edge case - party has all votes in only one constituency
    cc = make_constituencies(["C1", "C2"], [1000, 1000])
    parties = make_parties(["A"])
    rng = np.random.default_rng(999)
    # C1 has 100% turnout, C2 has 0% turnout
    turnout_pct = {"C1": 100.0, "C2": 0.0}

    # When
    ballot = VoteMatrix.generate(cc, parties, probabilities=[100.0], rng=rng, turnout=turnout_pct)
    ballot_evaluator = VoteMatrixAnalyzer(ballot.getVotes())
    importance_matrix = ballot_evaluator.getConstituencyImportanceMatrix()

    # Then
    # C1 has all votes, C2 has none
    # For C1: denominator is 0 (total - r_C1 = r_C1 - r_C1 = 0), so importance should be 0
    # For C2: r_ij is 0, so importance is 0
    assert importance_matrix.loc["C1", "A"] == 2000.0
    assert importance_matrix.loc["C2", "A"] == 0.0


def test_getConstituencyImportanceMatrix_balanced_distribution():
    # Given: Perfectly balanced distribution across constituencies
    # Create a ballot manually with known values
    cc = make_constituencies(["C1", "C2", "C3"], [100, 100, 100])
    parties = make_parties(["A", "B"])

    # Create ballot with specific vote distribution
    # Each constituency has same proportion: A=60, B=40
    votes_df = pd.DataFrame({
        "A": [60, 60, 60],
        "B": [40, 40, 40]
    }, index=["C1", "C2", "C3"])

    ballot = VoteMatrix(_votes=votes_df, _contestants={"A": parties[0], "B": parties[1]})

    # When
    ballot_evaluator = VoteMatrixAnalyzer(ballot.getVotes())
    importance_matrix = ballot_evaluator.getConstituencyImportanceMatrix()

    # Then
    # Since all constituencies have identical proportions,
    # importance should be equal for all constituencies for each party and should be 1
    for constituency in ["C1", "C2", "C3"]:
        assert math.isclose(importance_matrix.loc[constituency, "A"], 1, abs_tol=1e-10)
        assert math.isclose(importance_matrix.loc[constituency, "B"], 1, abs_tol=1e-10)


# ---- generate: contestants dict (mutant #318) ----

def test_generate_populates_contestants_dict():
    """Mutant #318: dict_contestants = None — _contestants is None, any use crashes."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, probabilities={"A": 60.0, "B": 40.0},
                             rng=np.random.default_rng(0), turnout=100.0)
    assert vm._contestants is not None
    assert len(vm._contestants) == 2


# ---- getContestantsByPercentDesc: empty/zero/boundary (mutants #321-334, #360) ----

def test_get_contestants_by_percent_desc_raises_on_empty():
    """Mutants #321 (or→and), #322 (XX-prefix): empty _votes raises anchored error."""
    vm = VoteMatrix(_votes=pd.DataFrame(), _contestants={})
    with pytest.raises(ValueError, match=r"^No votes available"):
        vm.getContestantsByPercentDesc()


def test_get_contestants_by_percent_desc_zero_votes():
    """Mutants #326 (total<0), #329 (pct=None), #334 (is None check) — zero total.

    All-zero matrix must return a Series of 0.0 without crashing.
    """
    vm = VoteMatrix(
        _votes=pd.DataFrame({"A": [0, 0], "B": [0, 0]}, index=["C1", "C2"]),
        _contestants={},
    )
    result = vm.getContestantsByPercentDesc(decimals=2)
    assert isinstance(result, pd.Series)
    assert (result == 0.0).all()


def test_get_contestants_by_percent_desc_values_sum_to_100():
    """Mutant #360: * instead of / in percentage formula — result would be huge."""
    cc = make_constituencies(["C1"], [10_000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, probabilities={"A": 70.0, "B": 30.0},
                             rng=np.random.default_rng(7), turnout=100.0)
    result = vm.getContestantsByPercentDesc()
    assert math.isclose(float(result.sum()), 100.0, abs_tol=0.5)


# ---- getContestantsByPercentThreshold: error message + boundary (mutants #345, #348, #352) ----

def test_get_contestants_by_percent_threshold_error_message():
    """Mutant #345: XX-prefix on threshold range error message."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0), turnout=100.0)
    with pytest.raises(ValueError, match=r"^threshold must be between"):
        vm.getContestantsByPercentThreshold(-1.0)


def test_get_contestants_by_percent_threshold_exact_boundary():
    """Mutant #348: csum > threshold (strict) — party AT exactly threshold is excluded.
    Mutant #352: cut_pos + 2 — one extra party returned.

    A=60%, B=40%. threshold=60 → original: only A; mutant #348: A+B; mutant #352: A+B.
    """
    vm = VoteMatrix(
        _votes=pd.DataFrame({"A": [600], "B": [400]}, index=["C1"]),
        _contestants={},
    )
    result = vm.getContestantsByPercentThreshold(60.0)
    assert len(result) == 1
    assert result.index[0] == "A"


# ---- show_votes_table_percent: replace(0) vs replace(1) (mutant #399) ----

def test_show_votes_table_percent_one_vote_constituency():
    """Mutant #399: replace(1, nan) instead of replace(0, nan) — 1-vote row gets NaN→0.

    A constituency with 1 total vote: A=1, B=0 → A should show 100%, B 0%.
    With the mutant, denominator 1 becomes NaN → A gets 0.0% (wrong).
    """
    vm = VoteMatrix(
        _votes=pd.DataFrame({"A": [1, 100], "B": [0, 100]}, index=["C1", "C2"]),
        _contestants={},
    )
    result = vm.show_votes_table_percent(styler=False)
    assert math.isclose(float(result.loc["C1", "A"]), 100.0, abs_tol=0.1)
    assert math.isclose(float(result.loc["C1", "B"]), 0.0, abs_tol=0.1)


# ---- turnout validation (mutants #430, #432, #441, #444, #446, #453, #456, #471) ----

def test_turnout_mapping_negative_value_raises():
    """Mutant #430: | → & — negative value alone no longer raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout={"C1": -1.0})


def test_turnout_mapping_over_100_raises():
    """Mutant #432: > 101.0 instead of > 100.0 — turnout=100.5 no longer raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout={"C1": 100.5})


def test_turnout_sequence_error_message_anchored():
    """Mutant #441: XX-prefix on length mismatch error message."""
    cc = make_constituencies(["C1", "C2"], [1000, 1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError, match=r"^When turnout is passed as a list"):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout=[50.0])


def test_turnout_sequence_negative_raises():
    """Mutant #444: | → & — negative value alone no longer raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout=[-5.0])


def test_turnout_sequence_over_100_raises():
    """Mutant #446: > 101.0 instead of > 100.0."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout=[100.5])


def test_turnout_scalar_zero_is_valid():
    """Mutant #453: not(1.0 <= m) instead of not(0.0 <= m) — turnout=0 raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, probabilities={"A": 60.0, "B": 40.0},
                             rng=np.random.default_rng(0), turnout=0.0)
    assert (vm.getVotes().sum().sum()) == 0


def test_turnout_scalar_over_100_raises():
    """Mutant #456: > 101.0 instead of > 100.0."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, rng=np.random.default_rng(0),
                            turnout=100.5)


def test_turnout_scalar_with_rng_none_does_not_crash():
    """Mutant #471: inverted rng check — with rng=None, rng.beta() crashes (None.beta)."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, probabilities={"A": 60.0, "B": 40.0},
                             turnout=50.0)
    assert vm.getVotes().sum().sum() > 0


# ---- probabilities validation (mutants #487, #492, #509, #511, #514, #517, #519, #521, #526) ----

def test_missing_probability_for_party_message_anchored():
    """Mutant #487: XX-prefix on 'Missing probability' error message."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    with pytest.raises(ValueError, match=r"^Missing probability for party"):
        VoteMatrix.generate(cc, parties, probabilities={"A": 100.0},
                            rng=np.random.default_rng(0), turnout=100.0)


def test_probability_sequence_length_mismatch_message_anchored():
    """Mutant #492: XX-prefix on sequence length mismatch error."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B", "C"])
    with pytest.raises(ValueError, match=r"^When probabilities is passed as a list"):
        VoteMatrix.generate(cc, parties, probabilities=[50.0, 50.0],
                            rng=np.random.default_rng(0), turnout=100.0)


def test_probability_over_100_raises():
    """Mutant #511: > 101.0 instead of > 100.0 — prob=100.5 no longer raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, probabilities={"A": 100.5, "B": 0.0},
                            rng=np.random.default_rng(0), turnout=100.0)


def test_probability_zero_sum_raises():
    """Mutant #514: sum < 0 instead of sum <= 0 — all-zero probs no longer raises."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    with pytest.raises(ValueError):
        VoteMatrix.generate(cc, parties, probabilities={"A": 0.0, "B": 0.0},
                            rng=np.random.default_rng(0), turnout=100.0)


def test_probabilities_exact_100_no_warning():
    """Mutant #517: isclose(101.0) — exact 100% sum treated as non-exact, warning issued.
    Mutant #519: /101.0 instead of /100.0 — probabilities scaled wrong.

    A=70%, B=30%: sum=100.0. Should convert without warning, A gets ~70% of votes.
    """
    cc = make_constituencies(["C1"], [100_000])
    parties = make_parties(["A", "B"])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vm = VoteMatrix.generate(cc, parties, probabilities={"A": 70.0, "B": 30.0},
                                 rng=np.random.default_rng(42), turnout=100.0)
        normalizing_warnings = [x for x in w if "Auto-normalizing to 100" in str(x.message)]
        assert len(normalizing_warnings) == 0
    pct = vm.getContestantsByPercentDesc()
    assert math.isclose(float(pct["A"]), 70.0, abs_tol=0.5)


def test_run_with_rng_none_does_not_crash():
    """Mutant #526: rng = None in _run (assignment to None) — later rng.beta() crashes."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm = VoteMatrix.generate(cc, parties, probabilities={"A": 60.0, "B": 40.0},
                             turnout=50.0)
    assert vm.getVotes().sum().sum() > 0


# ---- vote_matrix injection validation (mutants #531, #535, #538) ----

def test_injected_vote_matrix_missing_constituency_raises():
    """Mutant #531: set - → set + — TypeError instead of ValueError."""
    cc = make_constituencies(["C1", "C2"], [1000, 1000])
    parties = make_parties(["A", "B"])
    bad_vm = pd.DataFrame({"A": [100], "B": [50]}, index=["C1"])
    with pytest.raises((ValueError, TypeError)):
        VoteMatrix.generate(cc, parties, vote_matrix=bad_vm,
                            rng=np.random.default_rng(0), turnout=100.0)


def test_injected_vote_matrix_missing_contestant_raises():
    """Mutant #535: set - → set + — TypeError instead of ValueError."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    bad_vm = pd.DataFrame({"A": [100]}, index=["C1"])
    with pytest.raises((ValueError, TypeError)):
        VoteMatrix.generate(cc, parties, vote_matrix=bad_vm,
                            rng=np.random.default_rng(0), turnout=100.0)


def test_injected_vote_matrix_fillna_zero():
    """Mutant #538: fillna(1) instead of fillna(0) — absent parties get 1 vote."""
    cc = make_constituencies(["C1"], [1000])
    parties = make_parties(["A", "B"])
    vm_df = pd.DataFrame({"A": [100], "B": [50]}, index=["C1"])
    vm = VoteMatrix.generate(cc, parties, vote_matrix=vm_df,
                             rng=np.random.default_rng(0))
    assert int(vm.getVotes().loc["C1", "A"]) == 100
    assert int(vm.getVotes().loc["C1", "B"]) == 50


# ---- _validate_contestant_names (mutants #554, #558, #560, #562) ----

def test_contestant_list_type_validation_message():
    """Mutant #554: XX-prefix on 'contestants must be of type list' error."""
    with pytest.raises(ValueError, match=r"^contestants must be of type list"):
        VoteMatrix.generate(make_constituencies(["C1"], [1000]),
                            "not_a_list",
                            rng=np.random.default_rng(0))


def test_contestant_empty_name_raises_message():
    """Mutant #558 (XXXX strip check), #560 (XX-prefix on error)."""
    empty_c = Contestant(Contestant._PRIVATE, name="", members={}, member_vote_weights={})
    with pytest.raises(ValueError, match=r"^Contestant names must not be empty"):
        VoteMatrix.generate(make_constituencies(["C1"], [1000]),
                            [empty_c],
                            rng=np.random.default_rng(0))


def test_contestant_duplicate_name_raises_message():
    """Mutant #562: XX-prefix on duplicate name error."""
    a1 = Contestant.from_party("A")
    a2 = Contestant.from_party("A")
    with pytest.raises(ValueError, match=r"^Contestant names must be unique"):
        VoteMatrix.generate(make_constituencies(["C1"], [1000]),
                            [a1, a2],
                            rng=np.random.default_rng(0))

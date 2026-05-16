import math
import numpy as np
import pandas as pd
import pytest

from ipres.vote_matrix_analyzer import (
    VoteMatrixAnalyzer,
    getConstituencyImportanceMatrix,
)

def _create_votes_from_relative(relative_votes: pd.DataFrame, total_votes_per_constituency: int = 1000) -> pd.DataFrame:
    """Helper to create absolute votes matrix from relative votes for testing."""
    return (relative_votes * total_votes_per_constituency).round().astype(int)


def test_getConstituencyImportanceMatrix_basic():
    """Test basic importance calculation with known values."""
    # Given: Simple relative vote matrix with 3 constituencies and 2 parties
    relative_votes = pd.DataFrame({
        "A": [0.5, 0.3, 0.2],
        "B": [0.3, 0.4, 0.3]
    }, index=["C1", "C2", "C3"])

    # Create corresponding absolute votes matrix
    votes = pd.DataFrame({
        "A": [500, 300, 200],
        "B": [300, 400, 300]
    }, index=["C1", "C2", "C3"])

    # When
    importance_matrix = getConstituencyImportanceMatrix(relative_votes, votes)

    # Then
    # 1. Check shape
    assert importance_matrix.shape == relative_votes.shape
    assert list(importance_matrix.index) == ["C1", "C2", "C3"]
    assert list(importance_matrix.columns) == ["A", "B"]

    # 2. All values should be non-negative
    assert (importance_matrix >= 0).all().all()

    # 3. Verify formula: w_ij = (M-1) * r_ij / sum(r_kj for k != i)
    M = len(relative_votes)  # Number of constituencies
    for party in importance_matrix.columns:
        total_share = relative_votes[party].sum()
        for constituency in importance_matrix.index:
            r_ij = relative_votes.loc[constituency, party]
            expected_denominator = total_share - r_ij

            if expected_denominator > 0:
                expected_importance = (M - 1) * r_ij / expected_denominator
                actual_importance = importance_matrix.loc[constituency, party]
                assert math.isclose(actual_importance, expected_importance, abs_tol=1e-10), \
                    f"Importance for {constituency}, {party} mismatch"
            else:
                # Party has votes only in this constituency - should get high priority
                # importance = total_votes_in_system + votes_for_this_party_in_this_constituency
                total_votes = votes.sum().sum()
                expected = total_votes + votes.loc[constituency, party]
                assert importance_matrix.loc[constituency, party] == expected


def test_getConstituencyImportanceMatrix_single_constituency():
    """Test edge case where party has all votes in only one constituency."""
    # Given: Party A only has votes in C1
    relative_votes = pd.DataFrame({
        "A": [1.0, 0.0, 0.0],
        "B": [0.4, 0.3, 0.3]
    }, index=["C1", "C2", "C3"])

    votes = pd.DataFrame({
        "A": [1000, 0, 0],
        "B": [400, 300, 300]
    }, index=["C1", "C2", "C3"])

    # When
    importance_matrix = getConstituencyImportanceMatrix(relative_votes, votes)

    # Then
    # For C1: denominator is 0 (total - r_C1 = 1.0 - 1.0 = 0)
    # importance = total_votes + votes[C1, A] = 2000 + 1000 = 3000
    total_votes = votes.sum().sum()
    assert importance_matrix.loc["C1", "A"] == total_votes + 1000
    # For C2, C3: r_ij is 0, so importance is 0
    assert importance_matrix.loc["C2", "A"] == 0.0
    assert importance_matrix.loc["C3", "A"] == 0.0


def test_getConstituencyImportanceMatrix_balanced_distribution():
    """Test case with perfectly balanced distribution across constituencies.

    With the (M-1) normalization, balanced distributions should yield importance = 1.0
    for all constituencies, making values easier to interpret:
    - value = 1.0: average importance
    - value > 1.0: above average importance
    - value < 1.0: below average importance
    """
    # Given: Each constituency has identical proportions
    relative_votes = pd.DataFrame({
        "A": [0.6, 0.6, 0.6],
        "B": [0.4, 0.4, 0.4]
    }, index=["C1", "C2", "C3"])

    votes = pd.DataFrame({
        "A": [600, 600, 600],
        "B": [400, 400, 400]
    }, index=["C1", "C2", "C3"])

    # When
    importance_matrix = getConstituencyImportanceMatrix(relative_votes, votes)

    # Then
    # For party A: r_ij = 0.6 for all i, sum = 1.8, M = 3
    # w_ij = (M-1) * r_ij / (sum - r_ij) = 2 * 0.6 / 1.2 = 1.0
    for constituency in ["C1", "C2", "C3"]:
        assert math.isclose(importance_matrix.loc[constituency, "A"], 1.0, abs_tol=1e-10)
        # For party B: r_ij = 0.4, sum = 1.2, M = 3
        # w_ij = 2 * 0.4 / 0.8 = 1.0
        assert math.isclose(importance_matrix.loc[constituency, "B"], 1.0, abs_tol=1e-10)


# ---- getRelativeVoteMatrix: empty / error checks ----

def _simple_analyzer() -> VoteMatrixAnalyzer:
    votes = pd.DataFrame({"A": [600, 400], "B": [300, 700]}, index=["C1", "C2"])
    return VoteMatrixAnalyzer(votes)


def test_relative_vote_matrix_raises_on_empty_dataframe():
    """Mutants #937 (or→and) and #938 (XX-prefix): empty DataFrame must still raise.

    #937: 'or' → 'and' makes the check False when votes is not None but empty.
    #938: anchored match fails if message starts with 'XX'.
    """
    analyzer = VoteMatrixAnalyzer(pd.DataFrame())
    with pytest.raises(ValueError, match=r"^No votes available"):
        analyzer.getRelativeVoteMatrix()


def test_relative_vote_matrix_single_vote_constituency():
    """Mutant #941: replace(0, nan) → replace(1, nan).

    A constituency with exactly 1 total vote must get relative share 1.0,
    not NaN/0 as the mutant produces (it replaces the denominator 1 with NaN).
    """
    votes = pd.DataFrame({"A": [1, 500], "B": [0, 500]}, index=["C1", "C2"])
    result = VoteMatrixAnalyzer(votes).getRelativeVoteMatrix()
    assert math.isclose(result.loc["C1", "A"], 1.0, abs_tol=1e-10)
    assert math.isclose(result.loc["C1", "B"], 0.0, abs_tol=1e-10)


# ---- show_relative_vote_matrix ----

def test_show_relative_vote_matrix_returns_dataframe():
    """Mutant #950: relative_matrix = None → None.round() raises AttributeError."""
    result = _simple_analyzer().show_relative_vote_matrix()
    assert isinstance(result, pd.DataFrame)


def test_show_relative_vote_matrix_styler_not_none():
    """Mutant #961: styled = None → returns None instead of a Styler."""
    result = _simple_analyzer().show_relative_vote_matrix(styler=True)
    assert result is not None


# ---- show_constituency_importance_matrix ----

def test_show_constituency_importance_matrix_returns_dataframe():
    """Mutant #966: importance_matrix = None → None.round() raises AttributeError."""
    result = _simple_analyzer().show_constituency_importance_matrix()
    assert isinstance(result, pd.DataFrame)


def test_show_constituency_importance_matrix_styler_not_none():
    """Mutant #977: styled = None → returns None instead of a Styler."""
    result = _simple_analyzer().show_constituency_importance_matrix(styler=True)
    assert result is not None

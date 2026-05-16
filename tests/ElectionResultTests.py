"""Tests for ElectionResult display methods.

Each method call would fail with AttributeError or TypeError under the majority
of election_result.py mutants, which set intermediate DataFrames/variables to None.
"""
import numpy as np
import pandas as pd
import pytest

from ipres import (
    Election,
    ElectionConfig,
    ElectionEvaluator,
    SeatDistributionMethod,
    contestantsFromParties,
    SuperMajorityMargin,
    MarginUnit,
    ConstituenciesConfig,
    VoteMatrix,
    ElectionRoundInput,
)
from ipres.allocation import ConstituencyAllocationMethod
from ipres.election_config import (
    DrawLotsStrategy,
    QuotaCorrectionStrategy,
)
from ipres.election_result import ElectionResult


def _make_result() -> ElectionResult:
    """Run a small election and return the evaluated ElectionResult."""
    cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
        "constituency_name": ["C1", "C2"],
        "constituency_size": [10_000, 10_000],
    }))
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],
        parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
        seed=42,
    )
    vm_df = pd.DataFrame({"A": [700, 700], "B": [300, 300]}, index=["C1", "C2"])
    contestants = contestantsFromParties(["A", "B"])
    vm = VoteMatrix.generate(cc, contestants, vote_matrix=vm_df)
    election = Election(electionConfig=config)
    inp = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants={c.name: c for c in contestants},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        draw_lots_strategy=DrawLotsStrategy.RANDOM,
        rng=np.random.default_rng(42),
        vote_matrix=vm,
    )
    election.start(inp)
    evaluator = ElectionEvaluator(
        seat_distribution_method=SeatDistributionMethod.SAINTE_LAGUE,
        constituency_allocation_method=ConstituencyAllocationMethod.OPTIMAL,
        quota_correction_strategy=QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES,
        seed=42,
    )
    return evaluator.evaluate(election)


# ---- Cached result shared across tests ----
_result = None


def _get_result() -> ElectionResult:
    global _result
    if _result is None:
        _result = _make_result()
    return _result


# ---- ElectionResult dataclass field mutations (1418-1422) ----

def test_plotter_set_in_post_init():
    """Mutant #1422: _plotter stored under 'XX_plotterXX' — self._plotter remains None."""
    result = _get_result()
    assert result._plotter is not None


# ---- getGovernmentSeats (mutant #1423) ----

def test_government_seats_contains_winner_only():
    """Mutant #1423: 'in' → 'not in' — government seats become opposition seats."""
    result = _get_result()
    gov = result.getGovernmentSeats()
    winner_parties = result.election.getWinner().getContainedParties()
    for party in gov:
        assert party in winner_parties, f"{party} is not a winner party"


# ---- get_seat_distribution_table (mutants #1424-1432) ----

def test_seat_distribution_table_returns_styler():
    """Mutants #1424-1432: various None mutations crash when method is called."""
    from pandas.io.formats.style import Styler
    result = _get_result()
    table = result.get_seat_distribution_table()
    assert isinstance(table, Styler)


def test_seat_distribution_table_is_sorted_descending():
    """Mutant #1429: ascending=True instead of ascending=False — largest party last."""
    result = _get_result()
    table = result.get_seat_distribution_table()
    df = table.data
    values = list(df.iloc[:, 0])
    assert values == sorted(values, reverse=True)


# ---- get_constituency_assignment_table (mutants #1433-1461) ----

def test_constituency_assignment_table_party_sort_returns_styler():
    """Mutants #1434-1461: various None mutations crash when method is called."""
    from pandas.io.formats.style import Styler
    result = _get_result()
    table = result.get_constituency_assignment_table(sort_by="party")
    assert isinstance(table, Styler)


def test_constituency_assignment_table_constituency_sort_returns_styler():
    """Mutants #1445-1448: 'constituency' branch mutations."""
    from pandas.io.formats.style import Styler
    result = _get_result()
    table = result.get_constituency_assignment_table(sort_by="constituency")
    assert isinstance(table, Styler)


def test_constituency_assignment_table_invalid_sort_raises():
    """Mutant #1449: XX-prefix on error message — anchored match fails."""
    result = _get_result()
    with pytest.raises(ValueError, match=r"^sort_by must be 'party' or 'constituency'"):
        result.get_constituency_assignment_table(sort_by="invalid")


def test_constituency_assignment_table_has_correct_row_count():
    """Mutants #1439-1444: assignments=None or df=None — wrong row count or crash."""
    result = _get_result()
    table = result.get_constituency_assignment_table(sort_by="party")
    df = table.data
    # 2 constituencies + 1 summary row
    assert len(df) == 3


# ---- get_constituency_summary_table (mutants #1462-1488) ----

def test_constituency_summary_table_returns_styler():
    """Mutants #1462-1488: various None mutations crash when method is called."""
    from pandas.io.formats.style import Styler
    result = _get_result()
    table = result.get_constituency_summary_table()
    assert isinstance(table, Styler)


def test_constituency_summary_table_total_row_present():
    """Mutant #1480: XX-prefix on 'label_total' key — total row gets wrong text."""
    result = _get_result()
    table = result.get_constituency_summary_table()
    df = table.data
    # Total row is last; share should be 100.0
    last_row = df.iloc[-1]
    share_col = df.columns[-1]
    assert float(last_row[share_col]) == 100.0


def test_constituency_summary_table_correct_constituency_count():
    """Mutant #1470: total_constituencies=None — TypeError on division."""
    result = _get_result()
    table = result.get_constituency_summary_table()
    df = table.data
    # Total constituencies column (second col) in total row must equal 2
    total_row = df.iloc[-1]
    count_col = df.columns[1]
    assert int(total_row[count_col]) == 2


def test_constituency_assignment_table_no_extra_index_column():
    """Mutants #1443, #1447: reset_index(drop=False) adds an 'index' column."""
    result = _get_result()
    for sort_by in ("party", "constituency"):
        table = result.get_constituency_assignment_table(sort_by=sort_by)
        df = table.data
        assert "index" not in df.columns, f"Unexpected 'index' column for sort_by={sort_by!r}"


def test_constituency_summary_table_shares_sum_to_100():
    """Mutant #1472: / → * total_constituencies — share values explode."""
    result = _get_result()
    table = result.get_constituency_summary_table()
    df = table.data
    share_col = df.columns[-1]
    # All rows except the total row
    shares = df.iloc[:-1][share_col].astype(float)
    assert abs(shares.sum() - 100.0) < 0.2

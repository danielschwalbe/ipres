"""Tests for ElectionPlotter.

Uses the Agg (non-interactive) matplotlib backend. Most mutants set
intermediate variables to None or use wrong translation keys, causing
exceptions when plot_seat_share_pie() is called.
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
import matplotlib.pyplot as plt

from ipres import (
    Election,
    ElectionConfig,
    ElectionEvaluator,
    SeatDistributionMethod,
    Contestant,
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


def _make_result_with_coalition() -> ElectionResult:
    """Run an election where a coalition wins to exercise coalition code paths."""
    cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
        "constituency_name": ["C1", "C2", "C3", "C4"],
        "constituency_size": [10_000] * 4,
    }))
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
        seed=1,
    )
    # A+B coalition wins: A~40%, B~35%, C~25%
    vm_df = pd.DataFrame(
        {"A": [400, 400, 400, 400], "B": [350, 350, 350, 350], "C": [250, 250, 250, 250]},
        index=["C1", "C2", "C3", "C4"],
    )
    contestants = contestantsFromParties(["A", "B", "C"])
    vm = VoteMatrix.generate(cc, contestants, vote_matrix=vm_df)
    election = Election(electionConfig=config)
    inp = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants={c.name: c for c in contestants},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        draw_lots_strategy=DrawLotsStrategy.RANDOM,
        rng=np.random.default_rng(1),
        vote_matrix=vm,
    )
    ballot = election.start(inp)
    if not ballot.hasWinner():
        ballot.formCoalition("AB", ["A", "B"])

    evaluator = ElectionEvaluator(
        seat_distribution_method=SeatDistributionMethod.SAINTE_LAGUE,
        constituency_allocation_method=ConstituencyAllocationMethod.OPTIMAL,
        quota_correction_strategy=QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES,
        seed=1,
    )
    return evaluator.evaluate(election)


def _make_simple_result() -> ElectionResult:
    """Single-winner election without coalitions."""
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


# ---- Basic smoke tests (kill None-mutation mutants 1661-1750) ----

def test_plot_simple_returns_figure():
    """Mutants #1661, #1665-1750: self.result=None or wrong t() keys or None locals crash."""
    result = _make_simple_result()
    fig = result.plot_seat_share_pie(group_coalitions=False)
    assert fig is not None
    import matplotlib.figure
    assert isinstance(fig, matplotlib.figure.Figure)
    plt.close("all")


def test_plot_with_coalition_returns_figure():
    """Mutant #1680, #1730, #1740: None mutations in coalition code path crash."""
    result = _make_result_with_coalition()
    fig = result.plot_seat_share_pie(group_coalitions=True)
    assert fig is not None
    import matplotlib.figure
    assert isinstance(fig, matplotlib.figure.Figure)
    plt.close("all")


def test_plot_with_small_party_threshold():
    """Mutant #1740: large_parties=None — iteration over None crashes."""
    result = _make_simple_result()
    fig = result.plot_seat_share_pie(group_coalitions=True, min_seats_for_display=1)
    assert fig is not None
    plt.close("all")


# ---- Title handling (mutant #1820) ----

def test_plot_custom_title_is_used():
    """Mutant #1820: title if title is None — with title='Custom', label_seat_dist used instead."""
    result = _make_simple_result()
    fig = result.plot_seat_share_pie(title="My Custom Title")
    ax = fig.axes[0]
    assert ax.get_title() == "My Custom Title"
    plt.close("all")


def test_plot_default_title_is_not_none():
    """Mutant #1820: with title=None, title stays None (ax.set_title(None))."""
    result = _make_simple_result()
    fig = result.plot_seat_share_pie(title=None)
    ax = fig.axes[0]
    assert ax.get_title() != ""
    plt.close("all")

"""Tests for plotSharePie and plotSeatPie."""

import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.figure
import pytest
from ipres.plotting import plotSeatPie, plotSharePie


def test_plotSeatPie_returns_figure_with_correct_seat_labels():
    """plotSeatPie labels each wedge with the absolute seat count, not a percentage.

    Given seats=[30, 70] (total=100):
      correct:   int(round(30.0 * 100 / 100.0)) = 30  and  70
      mutant #88 (total_seats=None): TypeError in lambda
      mutant #89 (pct / total / 100):  30 / 100 / 100 = 0.003 → "0"
      mutant #90 (pct * total * 100):  30 * 100 * 100 = 300000
      mutant #91 (/ 101.0):            70 * 100 / 101 ≈ 69.3 → "69"
      mutant #92 (XX prefix):          "XX30XX" not "30"
      mutant #93 (autopct=None):       no autotext produced
      mutant #96 (axis 'XXequalXX'):   ValueError from matplotlib
    """
    fig = plotSeatPie(np.array([30, 70]), ["A", "B"], "Test")
    assert isinstance(fig, matplotlib.figure.Figure)
    ax = fig.axes[0]
    label_texts = {t.get_text() for t in ax.texts}
    assert "30" in label_texts, f"Expected '30' in pie labels, got {label_texts}"
    assert "70" in label_texts, f"Expected '70' in pie labels, got {label_texts}"

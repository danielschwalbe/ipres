"""Basic pie chart utilities for visualising vote and seat distributions."""

from __future__ import annotations
from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

__all__ = ['plotSharePie', 'plotSeatPie']

def plotSharePie(party_totals: Sequence[float] | np.ndarray, labels: Sequence[str], title: str) -> Figure:
    """Create a pie chart showing vote or seat share as percentages.

    Args:
        party_totals: Vote or seat counts for each contestant.
        labels: Contestant labels corresponding to each entry in ``party_totals``.
        title: Chart title.

    Returns:
        :class:`matplotlib.figure.Figure`
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(party_totals, labels=labels,
           autopct=lambda pct: f"{pct:.2f}%", startangle=90, counterclock=False)
    ax.axis('equal')
    ax.set_title(title)
    return fig


def plotSeatPie(seats_arr: Sequence[int] | np.ndarray, labels: Sequence[str], title: str) -> Figure:
    """Create a pie chart showing absolute seat counts instead of percentages.

    Args:
        seats_arr: Seat counts for each contestant.
        labels: Contestant labels corresponding to each entry in ``seats_arr``.
        title: Chart title.

    Returns:
        :class:`matplotlib.figure.Figure`
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    total_seats = int(np.sum(seats_arr))
    ax.pie(seats_arr, labels=labels,
           autopct=(lambda pct: f"{int(round(pct * total_seats / 100.0))}"),
           startangle=90, counterclock=False)
    ax.axis('equal')
    ax.set_title(title)
    return fig

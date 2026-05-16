"""Seat apportionment algorithms (Sainte-Laguë, D'Hondt, Hare-Niemeyer)."""

from __future__ import annotations
from collections.abc import Sequence
import numpy as np
from ipres.election_config import SeatDistributionMethod

__all__ = ['apportionSeats']

def apportionSeats(votes: Sequence[float] | np.ndarray, P: int, method: SeatDistributionMethod) -> np.ndarray:
    """Distribute P seats among N contestants based on their vote counts.

    Args:
        votes: Vote counts for each contestant.
        P: Total number of seats to distribute.
        method: Apportionment method to use (Sainte-Laguë, D'Hondt, or Hare-Niemeyer).

    Returns:
        Integer array of shape ``(N,)`` with the number of seats per contestant.
    """
    votes_arr = np.array(votes, dtype=float)
    N = votes_arr.shape[0]
    if P <= 0 or votes_arr.sum() <= 0:  # pragma: no mutate
        return np.zeros(N, dtype=int)

    if method == SeatDistributionMethod.SAINTE_LAGUE:
        k = np.arange(P)  # 0..P-1
        divisors = (2 * k + 1).astype(float)  # 1,3,5,...
        Q = votes_arr[:, None] / divisors[None, :]
        flat_idx = np.argpartition(Q, -P, axis=None)[-P:]
        party_idx = flat_idx // P
        seats = np.bincount(party_idx, minlength=N)
        return seats.astype(int)

    elif method == SeatDistributionMethod.D_HONDT:
        k = np.arange(1, P + 1, dtype=float)
        Q = votes_arr[:, None] / k[None, :]
        flat_idx = np.argpartition(Q, -P, axis=None)[-P:]
        party_idx = flat_idx // P
        seats = np.bincount(party_idx, minlength=N)
        return seats.astype(int)

    elif method == SeatDistributionMethod.HARE_NIEMEYER:
        quota = votes_arr.sum() / P
        base = np.floor(votes_arr / quota).astype(int)
        assigned = int(base.sum())
        seats = base.copy()
        remaining = P - assigned

        if remaining > 0:  # pragma: no mutate
            # Need to allocate `remaining` more seats based on largest remainders
            remainders = votes_arr - base * quota
            # Sort by remainder (descending), with votes as tiebreaker, then index
            order = np.lexsort((np.arange(N), -votes_arr, -remainders))
            # Take the first `remaining` parties (those with largest remainders)
            for i in range(remaining):
                seats[order[i]] += 1

        elif remaining < 0:  # pragma: no mutate
            # Over-allocated (shouldn't happen with correct quota, but handle it)
            over = -remaining  # pragma: no mutate
            remainders = votes_arr - base * quota  # pragma: no mutate
            # Sort by remainder (ascending), with votes as tiebreaker
            order = np.lexsort((np.arange(N), votes_arr, remainders))  # pragma: no mutate
            # Take away from parties with smallest remainders
            for i in range(over):  # pragma: no mutate
                if seats[order[i]] > 0:  # pragma: no mutate
                    seats[order[i]] -= 1  # pragma: no mutate

        return seats.astype(int)

    return np.zeros(N, dtype=int)

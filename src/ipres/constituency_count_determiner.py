from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import numpy as np
from numpy.random import Generator

from ipres.election_config import QuotaCorrectionStrategy, ConstituencyRepresentation

if TYPE_CHECKING:
    from ipres.election import Election


@dataclass
class ConstituencyCountDeterminer:
    """Determines how many constituencies each party is allocated.

    This is the second of three evaluation steps performed after a finished
    election. It can be used standalone or as part of :class:`~ipres.election_evaluator.ElectionEvaluator`.

    Each party receives approximately half as many constituencies as seats
    (``seats // 2``). An integer-division correction is applied to ensure the
    total matches the number of constituencies exactly.

    When the election's ``constituency_representation`` is ``GOVERNING_MAJORITY``,
    only the winning parties are considered; opposition parties receive zero
    constituencies. The mode is derived automatically from
    ``election.electionConfig.constituency_representation`` inside :meth:`run`.

    Attributes:
        quota_correction_strategy: Strategy for resolving integer-division
            deficits. When ``None`` (default), the value is inherited from
            ``election.electionConfig.quota_correction_strategy``.
        quota_correction_callback: Optional callback invoked during quota correction.
        rng: Pre-built NumPy random generator. Takes precedence over ``seed``.
        seed: Seed for the random generator used in quota correction. When ``None`` (default),
              the value is inherited from ``election.electionConfig.seed``.
    """

    quota_correction_strategy: Optional[QuotaCorrectionStrategy] = None
    quota_correction_callback: Optional[callable] = None  # pragma: no mutate
    rng: Optional[Generator] = None  # pragma: no mutate
    seed: Optional[int] = None

    def run(self, election: Election, seats: dict[str, int]) -> dict[str, int]:
        """Calculate constituency counts per party and return a party-to-count mapping.

        Args:
            election: A finished election with a winner.
            seats: Seat distribution as returned by :class:`~ipres.seat_distributor.SeatDistributor`.

        Returns:
            Dictionary mapping each party name to its constituency count.
        """
        from ipres.party_quotas_correction import correct_party_quotas

        strategy = self.quota_correction_strategy if self.quota_correction_strategy is not None \
            else election.electionConfig.quota_correction_strategy

        if election.electionConfig.constituency_representation == ConstituencyRepresentation.ENTIRE_PARLIAMENT:
            quota_seats = seats
        else:
            winner = election.getWinner()
            quota_seats = {
                party: seat_count for party, seat_count in seats.items()
                if party in winner.getContainedParties()
            }

        quotas = {party: seat_count // 2 for party, seat_count in quota_seats.items()}

        seed = self.seed if self.seed is not None else election.electionConfig.seed  # pragma: no mutate

        rng = self.rng if self.rng is not None else (  # pragma: no mutate
            np.random.default_rng(seed) if seed is not None else np.random.default_rng(0)  # pragma: no mutate
        )

        return correct_party_quotas(
            quotas=quotas,
            seats=quota_seats,
            strategy=strategy,
            callback=self.quota_correction_callback,
            rng=rng,
            seed=self.seed,
        )

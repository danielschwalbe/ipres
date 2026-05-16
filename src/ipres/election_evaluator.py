"""Election evaluator: computes seat distribution, constituency allocation, and final results."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from numpy.random import Generator

from ipres.allocation import ConstituencyAllocationMethod
from ipres.constituency_assigner import ConstituencyAssigner
from ipres.constituency_count_determiner import ConstituencyCountDeterminer
from ipres.election_config import SeatDistributionMethod, QuotaCorrectionStrategy
from ipres.seat_distributor import SeatDistributor

if TYPE_CHECKING:
    from ipres.election import Election


@dataclass
class ElectionEvaluator:
    """Evaluates a finished election to compute results.

    Orchestrates three evaluation steps in sequence:

    1. :class:`~ipres.seat_distributor.SeatDistributor` — distributes parliamentary seats.
    2. :class:`~ipres.constituency_count_determiner.ConstituencyCountDeterminer` — determines
       how many constituencies each party receives.
    3. :class:`~ipres.constituency_assigner.ConstituencyAssigner` — assigns specific
       constituencies to parties by relative importance.

    Each step can also be instantiated and called independently.

    ``constituency_representation`` and evaluation strategy defaults
    (``seat_distribution_method``, ``quota_correction_strategy``,
    ``constituency_allocation_method``) are derived automatically from
    ``election.electionConfig`` when the corresponding field is ``None``
    (the default). Set a field to a non-``None`` value to override the
    election-level default for a specific evaluation.
    """

    seat_distribution_method: Optional[SeatDistributionMethod] = None
    constituency_allocation_method: Optional[ConstituencyAllocationMethod] = None
    quota_correction_strategy: Optional[QuotaCorrectionStrategy] = None
    quota_correction_callback: Optional[callable] = None  # pragma: no mutate
    rng_for_allocation: Optional[Generator] = None
    seed: Optional[int] = None  # pragma: no mutate

    def evaluate(self, election: Election) -> 'ElectionResult':
        """Evaluate a finished election and return the results.

        Args:
            election: A finished election (must have a winner).

        Returns:
            ElectionResult containing seats, constituency assignments, and quotas.

        Raises:
            Exception: If the election is not finished.
        """
        from ipres.election_result import ElectionResult

        if not election.isFinished():
            raise Exception("Cannot evaluate an unfinished election. Election must have a winner.")

        seats = SeatDistributor(self.seat_distribution_method).run(election)

        seed = self.seed if self.seed is not None else election.electionConfig.seed  # pragma: no mutate

        party_constituency_counts = ConstituencyCountDeterminer(
            self.quota_correction_strategy,
            self.quota_correction_callback,
            self.rng_for_allocation,
            seed,
        ).run(election, seats)

        constituency_assignments = ConstituencyAssigner(
            self.constituency_allocation_method,
            self.rng_for_allocation,
            seed,
        ).run(election, party_constituency_counts)

        return ElectionResult(
            election=election,
            evaluator=self,
            seats=seats,
            constituency_assignments=constituency_assignments,
            party_constituency_counts=party_constituency_counts,
        )

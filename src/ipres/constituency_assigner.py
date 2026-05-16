from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import numpy as np
from numpy.random import Generator

from ipres.allocation import ConstituencyAllocationMethod, allocate_constituencies
from ipres.election_config import ConstituencyRepresentation
from ipres.vote_matrix_analyzer import VoteMatrixAnalyzer

if TYPE_CHECKING:
    from ipres.election import Election


@dataclass
class ConstituencyAssigner:
    """Assigns constituencies to parties based on relative importance.

    This is the third of three evaluation steps performed after a finished
    election. It can be used standalone or as part of :class:`~ipres.election_evaluator.ElectionEvaluator`.

    Relative importance is derived from the vote distribution across constituencies
    via :class:`~ipres.vote_matrix_analyzer.VoteMatrixAnalyzer`. The assignment
    algorithm is chosen via ``constituency_allocation_method``.

    When the election's ``constituency_representation`` is ``GOVERNING_MAJORITY``,
    only votes for the winning parties are used to compute importance. The mode
    is derived automatically from ``election.electionConfig.constituency_representation``
    inside :meth:`run`.

    Attributes:
        constituency_allocation_method: Algorithm used to assign constituencies.
            When ``None`` (default), the value is inherited from
            ``election.electionConfig.constituency_allocation_method``.
        rng: Pre-built NumPy random generator. Takes precedence over ``seed``.
        seed: Seed for the random generator used in allocation. When ``None`` (default), the value is inherited from
            ``election.electionConfig.seed``.
    """

    constituency_allocation_method: Optional[ConstituencyAllocationMethod] = None  # pragma: no mutate
    rng: Optional[Generator] = None  # pragma: no mutate
    seed: Optional[int] = None  # pragma: no mutate

    def run(self, election: Election, party_constituency_counts: dict[str, int]) -> dict[str, str]:
        """Assign constituencies to parties and return a constituency-to-party mapping.

        Args:
            election: A finished election with a winner.
            party_constituency_counts: Constituency counts per party as returned by
                :class:`~ipres.constituency_count_determiner.ConstituencyCountDeterminer`.

        Returns:
            Dictionary mapping each constituency name to the party it represents.
        """
        alloc_method = self.constituency_allocation_method if self.constituency_allocation_method is not None \
            else election.electionConfig.constituency_allocation_method

        vote_matrix = election.getFirstIteration().vote_matrix if not election.hadOutrightWinner() \
            else election.getLastIteration().vote_matrix

        if election.electionConfig.constituency_representation == ConstituencyRepresentation.ENTIRE_PARLIAMENT:
            votes = vote_matrix.getVotes()
        else:
            winner_parties = election.getWinner().getContainedParties()
            votes = vote_matrix.getVotes()[winner_parties]

        importance_matrix = VoteMatrixAnalyzer(votes).getConstituencyImportanceMatrix()

        seed = self.seed if self.seed is not None else election.electionConfig.seed  # pragma: no mutate
        rng = self.rng if self.rng is not None else np.random.default_rng(seed)  # pragma: no mutate

        return allocate_constituencies(
            importance_matrix=importance_matrix,
            quotas=party_constituency_counts,
            allocation_method=alloc_method,
            rng=rng,
        )

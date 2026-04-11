"""Seat distributor: first evaluation step that assigns parliamentary seats to contestants."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import numpy as np

from ipres.apportionment import apportionSeats
from ipres.election_config import SeatDistributionMethod

if TYPE_CHECKING:
    from ipres.election import Election
    from ipres.contestant import Contestant


@dataclass
class SeatDistributor:
    """Distributes parliamentary seats among parties based on election results.

    This is the first of three evaluation steps performed after a finished
    election. It can be used standalone or as part of :class:`~ipres.election_evaluator.ElectionEvaluator`.

    Two distribution paths exist:

    - **Path 1** (winner needs assigned majority): The winner is guaranteed the
      parliament majority seat share; remaining seats go proportionally to other
      parties based on first-round votes.
    - **Path 2** (outright winner above threshold): All seats are distributed
      proportionally based on the last round's votes.

    Attributes:
        seat_distribution_method: The apportionment method to use. When
            ``None`` (default), the value is inherited from
            ``election.electionConfig.seat_distribution_method``.
    """

    seat_distribution_method: Optional[SeatDistributionMethod] = None

    def run(self, election: Election) -> dict[str, int]:
        """Distribute parliamentary seats and return a mapping of party name to seat count.

        Args:
            election: A finished election with a winner.

        Returns:
            Dictionary mapping each party name to its seat count.
        """
        method = self.seat_distribution_method if self.seat_distribution_method is not None \
            else election.electionConfig.seat_distribution_method
        total_seats = election.electionConfig.parliamentarySeats

        if self._winner_needs_assigned_majority(election):
            winner = election.getWinner()
            gov_majority_seats = election.electionConfig.getParliamentMajoritySeats()
            remaining_seats = total_seats - gov_majority_seats

            first_iteration = election.getFirstIteration()
            first_votes = first_iteration.getOriginalContestantsVotes()
            other_votes = first_votes.drop(winner.getContainedParties())

            if len(other_votes) == 0 or remaining_seats == 0:
                return self._distribute_among_members(winner, total_seats, method)

            other_seats_array = apportionSeats(
                other_votes.values,
                remaining_seats,
                method,
            )

            result = self._distribute_among_members(winner, gov_majority_seats, method)
            for contestant_name, seats in zip(other_votes.index, other_seats_array):
                result[contestant_name] = int(seats)
            return result
        else:
            last_iteration = election.getLastIteration()
            last_votes = last_iteration.getContestantsVotesAfterPossibleCoalitions()
            contestants = last_iteration.getContestants()

            seats_array = apportionSeats(
                last_votes.values,
                total_seats,
                method,
            )

            return {
                member_name: member_seats
                for contestant_name, seats in zip(last_votes.index, seats_array)
                for member_name, member_seats in self._distribute_among_members(
                    contestants[contestant_name], int(seats), method
                ).items()
            }

    def _winner_needs_assigned_majority(self, election: Election) -> bool:
        """Return ``True`` if the winner must be assigned the parliament majority seats.

        This is the case when:
        - The election had no outright winner (decided by reduction or lot), or
        - The outright winner's vote share falls below the parliament majority threshold.
        """
        if not election.hadOutrightWinner():
            return True
        last_percentages = election.getLastIteration().getContestantsPercentagesAfterPossibleCoalitions()
        return last_percentages[election.getWinner().name] < election.electionConfig.getParliamentMajorityPercent()

    def _distribute_among_members(self, contestant: Contestant, seats: int, method: SeatDistributionMethod = SeatDistributionMethod.SAINTE_LAGUE) -> dict[str, int]:
        """Distribute seats among coalition members, or assign all to a single party.

        For single parties returns ``{party_name: seats}``.
        For coalitions distributes seats proportionally to member vote weights.
        """
        if contestant.isSingleParty():
            return {contestant.name: seats}

        party_weights = contestant.getMemberVoteWeightsForParties()
        party_names = list(party_weights.keys())
        weights_array = np.array([party_weights[name] for name in party_names])
        seats_array = apportionSeats(weights_array, seats, method)
        return dict(zip(party_names, seats_array))

"""Terminal round resolved by lot when two contestants are tied across two prior ballots."""

from __future__ import annotations
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

import pandas as pd
import numpy as np

from ipres.election_round import ElectionRound, ElectionRoundInput, DrawLotsStrategy
from ipres.contestant import Contestant

if TYPE_CHECKING:
    from ipres.election import Election


@dataclass
class DrawOfLots(ElectionRound):
    """A terminal election round decided by lot rather than by votes.

    Created when the same two contestants have faced each other in two
    consecutive ballot rounds without either reaching the super-majority
    threshold. No third ballot is cast — this draw-of-lots round is the
    third round. The winner is determined by the configured
    :class:`~ipres.election_round.DrawLotsStrategy`.

    Vote data is delegated to the preceding
    :class:`~ipres.ballot.Ballot` round via
    :meth:`getContestantsVotesAfterPossibleCoalitions`.

    Attributes:
        _round_input: The input that produced this draw.
        _contestants: The two contestants competing in this draw.
        _winner: The contestant selected by lot.
    """

    _round_input: ElectionRoundInput
    _contestants: dict[str, Contestant]
    _winner: Contestant

    # ---- Entry & lifecycle ----

    @classmethod
    def run(cls, _input: ElectionRoundInput) -> DrawOfLots:
        """Execute a draw-of-lots round and return the completed :class:`DrawOfLots`.

        Determines the winner according to the configured
        :class:`~ipres.election_round.DrawLotsStrategy` and registers the
        completed round with the parent Election.

        Args:
            _input: All parameters required for this round. ``previousRound``
                must not be ``None`` — votes are taken from there.

        Returns:
            A completed :class:`DrawOfLots` with ``_winner`` set.

        Raises:
            ValueError: If ``previousRound`` is ``None`` or the strategy is unknown.
        """
        if _input.previousRound is None:
            raise ValueError(
                "DrawOfLots requires a previous ballot round to delegate vote data to."
            )

        contestants = _input.contestants.copy()

        # Preserve shared references across deep-copy
        election_ref = _input.election
        rng_ref = _input.rng
        previous_round_ref = _input.previousRound
        copied_input = deepcopy(_input)
        copied_input.election = election_ref
        copied_input.rng = rng_ref
        copied_input.previousRound = previous_round_ref

        # Placeholder winner; will be replaced immediately
        draw = cls(
            _round_input=copied_input,
            _contestants=contestants,
            _winner=next(iter(contestants.values())),  # overwritten below
        )
        draw._round_input.round_number += 1
        draw._winner = draw._determine_winner()
        draw._round_input.election._append_round(draw)

        return draw

    # ---- ElectionRound abstract method implementations ----

    def getWinner(self) -> Contestant:
        """Return the contestant selected by lot."""
        return self._winner

    def hasWinner(self) -> bool:
        """Always ``True`` — a :class:`DrawOfLots` always produces a winner."""
        return True

    def hasNext(self) -> bool:
        """Always ``False`` — a :class:`DrawOfLots` is always the final round."""
        return False

    def getRoundNumber(self) -> int:
        """Return the 1-based index of this round within the election."""
        return self._round_input.round_number

    def getContestants(self) -> dict[str, Contestant]:
        """Return the two contestants that took part in this draw."""
        return self._contestants

    def getOriginalContestants(self) -> dict[str, Contestant]:
        """Return the contestants as recorded in the round input."""
        return self._round_input.contestants

    def getContestantsVotesAfterPossibleCoalitions(self) -> pd.Series:
        """Delegate vote totals to the preceding ballot round.

        A draw-of-lots round has no ballot of its own; vote data always
        comes from the most recent :class:`~ipres.ballot.Ballot`.

        Raises:
            ValueError: If ``previousRound`` is ``None`` (should not happen
                after :meth:`run` validation).
        """
        prev = self._round_input.previousRound
        if prev is None:
            raise ValueError(
                "Cannot retrieve votes: DrawOfLots has no previous ballot round."
            )
        return prev.getContestantsVotesAfterPossibleCoalitions()

    def getParticipatingParties(self) -> list[str]:
        """Return the names of all original parties taking part in this draw.

        For coalition contestants, each member party is listed individually.
        """
        return [
            party
            for contestant in self._contestants.values()
            for party in contestant.getContainedParties()
        ]

    def wasDecidedByLot(self) -> bool:
        """Always ``True`` — this round was decided by lot, not by vote count."""
        return True

    def getPreviousRound(self) -> Optional[ElectionRound]:
        """Return the preceding ballot round."""
        return self._round_input.previousRound

    def getNextRoundInput(self) -> None:
        """Always ``None`` — a :class:`DrawOfLots` is the terminal round."""
        return None

    # ---- Round metadata ----

    def getElection(self) -> Election:
        """Return the parent :class:`~ipres.election.Election`."""
        return self._round_input.election

    def getDrawLotsStrategy(self) -> DrawLotsStrategy:
        """Return the strategy that was used to determine the winner."""
        return self._round_input.draw_lots_strategy

    def getRoundNumber(self) -> int:
        """Return the 1-based index of this round within the election."""
        return self._round_input.round_number

    # ---- Internal — lot decision ----

    def _determine_winner(self) -> Contestant:
        """Select the winner according to the configured :class:`~ipres.election_round.DrawLotsStrategy`.

        Raises:
            ValueError: If the configured strategy is not recognised.
        """
        strategy = self._round_input.draw_lots_strategy
        candidates = self._contestants

        if strategy == DrawLotsStrategy.MARGINAL_LEAD:
            return self._decide_by_marginal_lead(
                candidates, self.getContestantsVotesAfterPossibleCoalitions()
            )
        if strategy == DrawLotsStrategy.RANDOM:
            return self._decide_by_random_draw(candidates, self._round_input.rng)

        raise ValueError(f"Unknown DrawLotsStrategy: {strategy}")

    @staticmethod
    def _decide_by_marginal_lead(
        candidates: dict[str, Contestant],
        votes: pd.Series,
    ) -> Contestant:
        """Return the candidate with the highest vote count from the previous ballot round."""
        candidate_votes = votes.loc[list(candidates.keys())]
        winner_name = candidate_votes.idxmax()
        return candidates[winner_name]

    @staticmethod
    def _decide_by_random_draw(
        candidates: dict[str, Contestant],
        rng: Optional[np.random.Generator],
    ) -> Contestant:
        """Return a randomly selected candidate using the provided RNG or Python's ``random``."""
        names = list(candidates.keys())
        winner_name = rng.choice(names) if rng is not None else random.choice(names)
        return candidates[winner_name]

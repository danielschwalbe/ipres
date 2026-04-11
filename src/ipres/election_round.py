"""Abstract base class and input container for ballot and draw-of-lots rounds."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Union, Optional, Mapping, TYPE_CHECKING
from collections.abc import Sequence as SequenceABC

import pandas as pd
import numpy as np

from ipres.contestant import Contestant
from ipres.constituencies_config import ConstituenciesConfig
from ipres.vote_matrix import VoteMatrix

if TYPE_CHECKING:
    from ipres.election import Election


class DrawLotsStrategy(Enum):
    """Strategy for breaking ties between two contestants across two consecutive rounds.

    - MARGINAL_LEAD: The marginal vote difference is treated as a random outcome —
      the contestant with the higher vote count in the most recent ballot round wins.
    - RANDOM: Break ties by uniform random selection (drawing of lots).
    """
    MARGINAL_LEAD = "marginal_lead"
    RANDOM = "random"


class ElectionRound(ABC):
    """Abstract base class for a single round within an iterative election.

    An election consists of one or more rounds. Each round either produces a winner
    (the contestant whose vote share meets the super-majority threshold) or reduces
    the field of contestants for the next round.

    Two concrete subtypes exist:

    - :class:`~ipres.ballot.Ballot` — a round decided by actual votes.
    - :class:`~ipres.draw_of_lots.DrawOfLots` — a round decided by lot when two
      contestants are tied across two consecutive ballot rounds.

    Polymorphism via :meth:`getContestantsVotesAfterPossibleCoalitions` is the key
    mechanism: ``Ballot`` reads from its own :class:`~ipres.vote_matrix.VoteMatrix`,
    while ``DrawOfLots`` delegates to the previous round.
    """

    @abstractmethod
    def getWinner(self) -> Optional[Contestant]:
        """Return the winning contestant, or ``None`` if no winner was found."""

    @abstractmethod
    def hasWinner(self) -> bool:
        """Return ``True`` if a winner was determined in this round."""

    @abstractmethod
    def hasNext(self) -> bool:
        """Return ``True`` if the election continues with another round after this one."""

    @abstractmethod
    def getRoundNumber(self) -> int:
        """Return the 1-based index of this round within the election."""

    @abstractmethod
    def getContestants(self) -> dict[str, Contestant]:
        """Return the current contestants, including any coalitions formed after the round."""

    @abstractmethod
    def getOriginalContestants(self) -> dict[str, Contestant]:
        """Return the contestants as they were at the start of this round, before coalition formation."""

    @abstractmethod
    def getContestantsVotesAfterPossibleCoalitions(self) -> pd.Series:
        """Return vote totals for each current contestant, merging coalition member votes.

        For :class:`~ipres.ballot.Ballot`, totals come from its own vote matrix.
        For :class:`~ipres.draw_of_lots.DrawOfLots`, totals are delegated to the
        previous ballot round.
        """

    def getContestantsRelativeVotesAfterPossibleCoalitions(self) -> pd.Series:
        """Return each contestant's share of the total votes cast, as a value between 0 and 1.

        Coalition members' votes are merged before computing shares, so the
        values sum to exactly 1.0 across all current contestants.

        Raises:
            KeyError: If a contestant or coalition member name is missing from the ballot.
        """
        votes = self.getContestantsVotesAfterPossibleCoalitions()
        return votes / votes.sum()

    def getContestantsPercentagesAfterPossibleCoalitions(self) -> pd.Series:
        """Return each contestant's share of the total votes cast, as a percentage (0–100).

        Equivalent to :meth:`getContestantsRelativeVotesAfterPossibleCoalitions` scaled by 100.
        Values sum to 100.0 across all current contestants.

        Raises:
            KeyError: If a contestant or coalition member name is missing from the ballot.
        """
        return self.getContestantsRelativeVotesAfterPossibleCoalitions() * 100.0

    @abstractmethod
    def getParticipatingParties(self) -> list[str]:
        """Return the names of all original parties taking part in this round.

        For coalition contestants, each member party is listed individually.
        """

    @abstractmethod
    def wasDecidedByLot(self) -> bool:
        """Return ``True`` if the winner was chosen by lot rather than by vote count.

        :class:`~ipres.ballot.Ballot` always returns ``False``;
        :class:`~ipres.draw_of_lots.DrawOfLots` always returns ``True``.
        """

    @abstractmethod
    def getPreviousRound(self) -> Optional[ElectionRound]:
        """Return the preceding round, or ``None`` if this is the first round."""

    @abstractmethod
    def getNextRoundInput(self) -> Optional[ElectionRoundInput]:
        """Return the pre-built input for the next round, or ``None`` if the election is finished.

        Always ``None`` for :class:`~ipres.draw_of_lots.DrawOfLots` (which is always terminal).
        """

    # ---- Factory ----

    @classmethod
    def run(cls, _input: ElectionRoundInput) -> ElectionRound:
        """Factory method: create the appropriate :class:`ElectionRound` subtype for the given input.

        Checks whether the lot condition is met (same two contestants across two
        consecutive rounds without a winner). If so, a
        :class:`~ipres.draw_of_lots.DrawOfLots` round is created; otherwise a
        :class:`~ipres.ballot.Ballot` round.

        Args:
            _input: All parameters required for the new round.

        Returns:
            A completed :class:`ElectionRound` — either a :class:`~ipres.ballot.Ballot`
            or a :class:`~ipres.draw_of_lots.DrawOfLots`.

        Raises:
            NotImplementedError: If the lot condition is met and ``DrawOfLots`` has not
                yet been implemented (Phase 4).
        """
        if cls._lot_required(_input):
            from ipres.draw_of_lots import DrawOfLots
            return DrawOfLots.run(_input)
        from ipres.ballot import Ballot
        return Ballot.run(_input)

    @staticmethod
    def _lot_required(_input: ElectionRoundInput) -> bool:
        """Return ``True`` if the next round must be decided by lot.

        Lot is required when exactly two contestants remain and the same two
        have already competed in two preceding rounds without a winner.
        """
        if _input.numberOfContestants() != 2:
            return False
        prev = _input.previousRound
        if prev is None:
            return False
        if set(prev.getContestants()) != set(_input.contestants):
            return False
        prev2 = prev.getPreviousRound()
        if prev2 is None:
            return False
        return set(prev2.getContestants()) == set(_input.contestants)


@dataclass
class ElectionRoundInput:
    """Input container for a single election round.

    Bundles all parameters required by :meth:`ElectionRound.run`. The election
    reference and the random number generator are intentionally not deep-copied
    when a round creates the input for its successor, so that shared state
    (round list, RNG sequence) stays consistent across the chain.

    Attributes:
        election: The parent :class:`~ipres.election.Election` instance.
        constituencies_config: Constituency definitions and sizes.
        contestants: Contestants competing in this round, keyed by name.
        probabilities: Optional vote-share probabilities (mapping or sequence).
        rng: NumPy random generator; ``None`` creates a fresh default generator.
        turnout: Optional per-constituency turnout (mapping, sequence, or scalar).
        ballot_majority_percent: Vote-share threshold required to win.
        draw_lots_strategy: Strategy used when the round must be decided by lot.
        vote_matrix: Optional pre-generated :class:`~ipres.vote_matrix.VoteMatrix`
            to inject instead of simulating a new ballot.
        round_number: 0-based index incremented to 1-based inside the round.
        previousRound: The preceding :class:`ElectionRound`, or ``None`` for the first.
    """
    election: Election
    constituencies_config: ConstituenciesConfig
    contestants: dict[str, Contestant] = field(default_factory=dict)
    probabilities: Optional[Union[Mapping[str, float], SequenceABC[float]]] = None
    rng: Optional[np.random.Generator] = None
    turnout: Optional[Union[Mapping[str, float], SequenceABC[float], float]] = None
    ballot_majority_percent: float = 52.0
    draw_lots_strategy: DrawLotsStrategy = DrawLotsStrategy.RANDOM
    vote_matrix: Optional[VoteMatrix] = None
    round_number: int = 0
    previousRound: Optional[ElectionRound] = None

    def numberOfContestants(self) -> int:
        """Return the number of contestants registered for this round."""
        return len(self.contestants)

    def with_votes(
        self,
        votes: Union[dict[str, int], dict[str, dict[str, int]]],
    ) -> "ElectionRoundInput":
        """Return a copy of this input with a fixed vote matrix injected.

        Args:
            votes: For a single constituency, a mapping of contestant name to
                vote count, e.g. ``{'A': 35, 'B': 33, 'C': 32}``.
                For multiple constituencies, a nested mapping
                ``{constituency_name: {contestant_name: vote_count}}``.

        Returns:
            A new :class:`ElectionRoundInput` with ``vote_matrix`` set to the
            provided counts and ``probabilities`` cleared.

        Raises:
            ValueError: If a flat dict is passed but more than one constituency
                is configured.
        """
        constituency_names = self.constituencies_config.getConstituencyNames()
        if votes and isinstance(next(iter(votes.values())), dict):
            df = pd.DataFrame(votes).T.reindex(constituency_names).fillna(0).astype(int)
        else:
            if len(constituency_names) != 1:
                raise ValueError(
                    "Flat votes dict requires exactly 1 constituency; "
                    f"got {list(constituency_names)}. Use a nested dict instead."
                )
            df = pd.DataFrame([votes], index=constituency_names)
        return replace(
            self,
            vote_matrix=VoteMatrix(_votes=df, _contestants=self.contestants),
            probabilities=None,
        )

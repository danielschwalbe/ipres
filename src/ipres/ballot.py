"""Ballot round execution and result evaluation for multi-round elections."""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from copy import deepcopy
from typing import Optional, TYPE_CHECKING
import pandas as pd
import numpy as np

from ipres.election_round import ElectionRound, ElectionRoundInput, DrawLotsStrategy
from ipres.election_config import Language
from ipres.strings import t, format_number
from ipres.vote_matrix import VoteMatrix
from ipres.contestant import Contestant
from ipres.plotting import plotSharePie

if TYPE_CHECKING:
    from ipres.election import Election


@dataclass
class Ballot(ElectionRound):
    """A single voting round in an iterative election, decided by actual votes.

    Instances are created exclusively via :meth:`Ballot.run`. Each completed
    ballot registers itself with the parent :class:`~ipres.election.Election`
    and, if no winner was found, stores a ready-to-use
    :class:`~ipres.election_round.ElectionRoundInput` for the next round.

    :meth:`getContestantsVotesAfterPossibleCoalitions` reads directly from the
    ballot's :class:`~ipres.vote_matrix.VoteMatrix`. Compare this with
    :class:`~ipres.draw_of_lots.DrawOfLots`, which delegates to the previous round.

    Attributes:
        _election_round_input: The input that produced this ballot.
        _contestants: Current contestants, reflecting any coalitions formed after
            :meth:`run` completed.
        _vote_matrix: The vote data collected in this round.
        _winner: The winning contestant, or ``None`` if no winner was found.
        _next_round_input: Pre-built input for the next round, or ``None`` if
            the election is finished.
    """

    _election_round_input: ElectionRoundInput
    _contestants: dict[str, Contestant]
    _vote_matrix: VoteMatrix
    _winner: Optional[Contestant] = field(default=None)
    _next_round_input: Optional[ElectionRoundInput] = field(default=None)

    # ---- Entry & lifecycle ----

    @classmethod
    def run(cls, _input: ElectionRoundInput) -> Ballot:
        """Execute one ballot round and return the completed :class:`Ballot`.

        Deep-copies the input to isolate this round's state while preserving
        the shared election reference and RNG. Uses a pre-generated
        :class:`~ipres.vote_matrix.VoteMatrix` when provided; otherwise
        generates a new one from the constituencies config. Registers the
        completed ballot with the parent Election.

        Args:
            _input: All parameters required for this round.

        Returns:
            A completed :class:`Ballot` with winner or next-round input set.

        Raises:
            ValueError: If fewer than two contestants are provided.
        """
        if _input.numberOfContestants() < 2:
            raise ValueError("At least two contestants are required for a ballot.")

        contestants = _input.contestants.copy()

        # Deep-copy input but preserve shared references (election, rng, previousRound)
        election_ref = _input.election
        rng_ref = _input.rng
        previous_round_ref = _input.previousRound
        copied_input = deepcopy(_input)
        copied_input.election = election_ref
        copied_input.rng = rng_ref
        copied_input.previousRound = previous_round_ref

        # Unwrap VoteMatrix to DataFrame when injecting pre-built vote data
        raw_vote_matrix = (
            _input.vote_matrix.getVotes() if _input.vote_matrix is not None else None
        )
        vote_matrix = VoteMatrix.generate(
            _input.constituencies_config,
            list(contestants.values()),
            _input.probabilities,
            _input.rng,
            _input.turnout,
            raw_vote_matrix,
        )

        ballot = cls(
            _election_round_input=copied_input,
            _contestants=contestants,
            _vote_matrix=vote_matrix,
        )
        ballot._election_round_input.round_number += 1
        ballot._evaluateResult()
        ballot._election_round_input.election._append_round(ballot)

        return ballot

    # ---- ElectionRound abstract method implementations ----

    def getWinner(self) -> Optional[Contestant]:
        """Return the winning contestant, or ``None`` if no winner was found."""
        return self._winner

    def hasWinner(self) -> bool:
        """Return ``True`` if a winner has been determined in this round."""
        return self._winner is not None

    def hasNext(self) -> bool:
        """Return ``True`` if the election continues with another round."""
        return not self.hasWinner()

    def getRoundNumber(self) -> int:
        """Return the 1-based index of this round within the election."""
        return self._election_round_input.round_number

    def getContestants(self) -> dict[str, Contestant]:
        """Return the current contestants, including any coalitions formed after :meth:`run`."""
        return self._contestants

    def getOriginalContestants(self) -> dict[str, Contestant]:
        """Return the contestants as they were at the start of this round, before coalition formation."""
        return self._election_round_input.contestants

    def getContestantsVotesAfterPossibleCoalitions(self) -> pd.Series:
        """Return vote totals for the current contestants, merging coalition member votes.

        For coalitions formed after :meth:`run`, each coalition's total is the
        sum of its members' individual ballot votes.

        Raises:
            KeyError: If a contestant or coalition member name is missing from the ballot.
        """
        totals = self._vote_matrix.getVotes().sum(axis=0)
        result = {
            name: int(self._get_effective_original_votes(c, totals))
            for name, c in self._contestants.items()
        }
        return pd.Series(result, dtype=int)

    def wasDecidedByLot(self) -> bool:
        """Always returns ``False`` — a :class:`Ballot` is decided by votes, not by lot."""
        return False

    def getPreviousRound(self) -> Optional[ElectionRound]:
        """Return the preceding round, or ``None`` if this is the first round."""
        return self._election_round_input.previousRound

    @property
    def vote_matrix(self) -> VoteMatrix:
        """The vote data collected in this round."""
        return self._vote_matrix

    # ---- Round metadata ----

    def getElection(self) -> Election:
        """Return the parent :class:`~ipres.election.Election` that owns this ballot."""
        return self._election_round_input.election

    def getBallotMajorityPercent(self) -> float:
        """Return the vote-share threshold (in percent) required to win this round."""
        return self._election_round_input.ballot_majority_percent

    def getDrawLotsStrategy(self) -> DrawLotsStrategy:
        """Return the lot-drawing strategy configured for this round."""
        return self._election_round_input.draw_lots_strategy

    def _lang(self) -> Language:
        """Return the display language configured in the parent election."""
        return self.getElection().electionConfig.language

    def getParticipatingParties(self) -> list[str]:
        """Return the names of all original parties taking part in this round.

        For coalition contestants, each member party is listed individually.
        """
        return [
            party
            for contestant in self._contestants.values()
            for party in contestant.getContainedParties()
        ]

    # ---- Round chain navigation ----

    def getFirstRound(self) -> ElectionRound:
        """Walk back through the round chain and return the very first round."""
        current: ElectionRound = self
        while current.getPreviousRound() is not None:
            current = current.getPreviousRound()
        return current

    def getNextRoundInput(self) -> Optional[ElectionRoundInput]:
        """Return the pre-built :class:`~ipres.election_round.ElectionRoundInput` for the
        next round, or ``None`` if the election is finished."""
        return self._next_round_input

    def needsDecisionByLotInNextRound(self) -> bool:
        """Return ``True`` if the next round would be resolved by lot.

        This is the case when no winner has been found, exactly two contestants
        remain, and the previous round had the same two contestants (meaning a
        third identical round would trigger the lot condition).
        """
        return (
            not self.hasWinner()
            and len(self._contestants) == 2
            and self._hadPreviousRoundSameContestants()
        )

    # ---- Vote data ----

    def getOriginalContestantsVotes(self) -> pd.Series:
        """Return the total votes for each original contestant across all constituencies.

        Original contestants are those present at the start of the round, before
        any coalitions are formed.

        Returns:
            Series with contestant names as index and integer vote totals as values.
        """
        return self._vote_matrix.getVotes().sum(axis=0)

    def getContestantsByPercentageDesc(
        self,
        threshold: Optional[float] = None,
        decimals: Optional[int] = None,
    ) -> pd.Series:
        """Return contestants sorted by vote share in percent, highest first.

        Args:
            threshold: If given, return only the leading contestants whose
                cumulative vote share first reaches or exceeds this value
                (0–100). If the threshold is never reached, the full list
                is returned.
            decimals: Number of decimal places to round to. ``None`` skips
                rounding.

        Returns:
            Series with contestant names as index and vote-share percentages
            as values, sorted descending.

        Raises:
            ValueError: If ``threshold`` is outside [0, 100].
        """
        votes = self.getContestantsVotesAfterPossibleCoalitions().astype(float)
        total = float(votes.sum())
        if total <= 0.0:
            pct = pd.Series(0.0, index=votes.index, dtype=float)
        else:
            pct = (votes / total) * 100.0
        if decimals is not None:
            pct = pct.round(decimals)
        pct = pct.sort_values(ascending=False, kind="mergesort")

        if threshold is None:
            return pct
        if threshold < 0 or threshold > 100:
            raise ValueError("threshold must be between 0 and 100 (percent).")
        if pct.empty:
            return pct
        csum = pct.cumsum()
        mask = csum >= threshold
        if mask.any():
            cut_pos = int(np.argmax(mask.to_numpy()))
            return pct.iloc[: cut_pos + 1]
        return pct

    # ---- Coalition management ----

    def formCoalition(self, name: str, contestants: list[Contestant] | list[str]) -> None:
        """Form a coalition from existing contestants in this round.

        Replaces the given contestants with a single new coalition contestant and
        re-evaluates the round result. Vote weights for the coalition are
        proportional to each member's original ballot votes.

        Members may be single parties, coalitions from a previous round, or
        coalitions formed within the current round. Arbitrary nesting is permitted.

        Args:
            name: Display name for the new coalition.
            contestants: The contestants to merge, given either as
                :class:`~ipres.contestant.Contestant` objects or as their names.

        Raises:
            ValueError: If any contestant is not part of this round, or if the
                coalition would include all contestants and no party has been
                eliminated since the first round.
        """
        if isinstance(contestants[0], str):
            contestants = [self._contestants[c] for c in contestants]

        names = {c.name for c in contestants}
        extra = names - self._contestants.keys()
        if extra:
            raise ValueError(f"Not among the contestants in this round: {sorted(extra)}")

        remaining = set(self._contestants.keys()) - names
        if len(remaining) < 1:
            if (len(self.getOriginalContestantsVotes())
                    >= len(self.getFirstRound().getOriginalContestantsVotes())):
                raise ValueError(
                    "At least two contestants must compete. "
                    "All contestants cannot form a single coalition."
                )

        vote_weights = self._calculate_member_vote_weights(contestants)

        for n in names:
            del self._contestants[n]

        members = {c.name: c for c in contestants}
        self._contestants[name] = Contestant.as_coalition(
            name, members, member_vote_weights=vote_weights
        )
        self._evaluateResult()

    def resetCoalitions(self) -> None:
        """Revert the contestant list to the state at the start of this round, discarding all coalitions."""
        self._contestants = self._election_round_input.contestants.copy()
        self._evaluateResult()

    # ---- Results visualisation ----

    def show_results_table(
        self,
        styler: bool = False,
        decimals: int = 2,
        print_table: bool = False,
    ):
        """Return a table of vote counts and percentages for the current contestants.

        Contestants are sorted by vote share (descending). Column names and captions
        use the language configured in ``ElectionConfig.language`` (``Language.DE`` by default).

        Args:
            styler: If ``True``, return a pandas Styler with formatted columns
                and a caption; if ``False``, return a plain DataFrame.
            decimals: Number of decimal places for the percentage column.
            print_table: If ``True``, also print the DataFrame to stdout.

        Returns:
            A :class:`pandas.DataFrame` or :class:`pandas.io.formats.style.Styler`
            depending on ``styler``.
        """
        lang = self._lang()
        votes = self.getContestantsVotesAfterPossibleCoalitions()
        total = int(votes.sum())
        if total <= 0:
            perc = pd.Series(0.0, index=votes.index, dtype=float)
        else:
            perc = (votes.astype(float) / float(total)) * 100.0
        if decimals is not None:
            perc = perc.round(decimals)
        col_votes = t("col_votes", lang)
        col_percent = t("col_percent", lang)
        df = pd.DataFrame({col_votes: votes.astype(int), col_percent: perc.astype(float)})
        df = df.sort_values(by=[col_percent, col_votes], ascending=[False, False], kind="mergesort")

        if styler:
            sty = df.style.format({
                col_votes: "{:,.0f}".format,
                col_percent: (lambda v: f"{v:.{decimals}f}%") if decimals is not None else str,
            }).set_caption(t("caption_results", lang, total=format_number(total, lang)))
            return sty

        if print_table:
            with pd.option_context("display.max_rows", None, "display.max_columns", None):
                print(df.to_string())
        return df

    def plot_vote_share_pie(
        self,
        title: Optional[str] = None,
        min_percent: float = 1.0,
    ):
        """Return a pie chart of the vote-share distribution for this round.

        Contestants whose share falls below ``min_percent`` are grouped into a
        single "Sonstige" (other) slice.

        Args:
            title: Chart title. Defaults to a generated string showing the
                total vote count and round number.
            min_percent: Minimum share a contestant must have to appear
                individually (default 1.0%).

        Returns:
            :class:`matplotlib.figure.Figure`
        """
        votes = self.getContestantsVotesAfterPossibleCoalitions()
        total_votes = votes.sum()

        percentages = votes / total_votes * 100.0
        votes_sorted = votes.sort_values(ascending=False)

        major_parties: list[str] = []
        major_votes: list[int] = []
        small_votes_total = 0

        for party, vote_count in votes_sorted.items():
            if percentages[party] >= min_percent:
                major_parties.append(party)
                major_votes.append(vote_count)
            else:
                small_votes_total += vote_count

        lang = self._lang()
        if small_votes_total > 0:
            major_parties.append(t("label_other", lang))
            major_votes.append(small_votes_total)

        if title is None:
            title = t(
                "title_vote_dist_round", lang,
                round_number=self.getRoundNumber(),
                total=format_number(int(total_votes), lang),
            )

        return plotSharePie(np.array(major_votes), major_parties, title)

    # ---- Internal — result evaluation ----

    def _evaluateResult(self) -> None:
        """Determine the outcome of this round after ballot counting or coalition changes.

        Resets winner and next-round input, then checks whether the leading contestant
        reaches the super-majority threshold. The candidate pool for the next round is
        determined by taking the top contestants whose cumulative vote share covers the
        first two-thirds of all votes.
        """
        self._next_round_input = None
        self._winner = None

        contestants_until_threshold = self.getContestantsByPercentageDesc(
            threshold=2.0 / 3.0 * 100
        )

        if contestants_until_threshold.iloc[0] >= self.getBallotMajorityPercent():
            winner_name = contestants_until_threshold.index[0]
            self._winner = self._contestants[winner_name]
            return

        if contestants_until_threshold.empty or len(contestants_until_threshold) == 0:
            raise ValueError("No contestants remain after threshold.")
        if len(contestants_until_threshold) > len(self._contestants):
            raise ValueError("More contestants remain after threshold than before.")

        next_contestants = {
            name: self._contestants[name]
            for name in list(contestants_until_threshold.index)
        }
        self._next_round_input = replace(
            self._election_round_input,
            contestants=next_contestants,
            previousRound=self,
            vote_matrix=None,   # force new vote matrix generation
            probabilities=None, # force random probabilities
        )

    # ---- Internal — lot detection helpers ----

    def _hadPreviousRoundSameContestants(self) -> bool:
        """Return ``True`` if the immediately preceding round had the same contestant set."""
        prev = self.getPreviousRound()
        if prev is None:
            return False
        return self._contestants == prev.getContestants()

    # ---- Internal — coalition helpers ----

    def _get_effective_original_votes(
        self,
        contestant: Contestant,
        original_votes: pd.Series,
    ) -> float:
        """Return the effective original votes for a contestant.

        For original contestants (including coalitions from previous rounds),
        returns their ballot votes directly. For coalitions formed within the
        current round, recursively sums the original votes of their members.

        Args:
            contestant: The contestant to look up.
            original_votes: Ballot votes indexed by original contestant name.

        Returns:
            The effective vote total as a float.
        """
        if contestant.name in original_votes.index:
            return float(original_votes[contestant.name])
        return sum(
            self._get_effective_original_votes(m, original_votes)
            for m in contestant.members.values()
        )

    def _calculate_member_vote_weights(
        self, contestants: list[Contestant]
    ) -> dict[str, float]:
        """Return a vote-weight fraction for each coalition member, summing to 1.0.

        Fractions are proportional to each member's effective original ballot votes.
        If all members received zero votes, equal weights are assigned.

        Args:
            contestants: The contestants that will form the coalition.

        Returns:
            A dict mapping each contestant's name to its weight fraction.
        """
        original_votes = self.getOriginalContestantsVotes()
        member_votes = {
            c.name: self._get_effective_original_votes(c, original_votes)
            for c in contestants
        }
        total = sum(member_votes.values())

        if total == 0:
            equal = 1.0 / len(contestants)
            return {c.name: equal for c in contestants}

        return {name: v / total for name, v in member_votes.items()}

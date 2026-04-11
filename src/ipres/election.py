"""Main election controller orchestrating iterative ballot and draw-of-lots rounds."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional
from ipres.election_config import ElectionConfig
from ipres.election_round import ElectionRound, ElectionRoundInput
from ipres.ballot import Ballot
from ipres.contestant import Contestant, contestantsDictFromParties
import numpy as np

@dataclass
class Election:
    """Represents a complete election and manages its iterative execution.

    An election consists of one or more rounds of proportional voting.
    Voting continues until a party or coalition wins a government majority.
    Result evaluation (seat distribution, constituency allocation) is handled
    separately by ElectionEvaluator and ElectionResult.

    Attributes:
        electionConfig: Global configuration for this election (constituencies,
            parties, majority threshold, etc.).
        iterations: Read-only tuple of all completed election rounds,
            in chronological order.

    Example — automatic (simplest case):
        >>> election = Election(electionConfig=config)
        >>> final = election.run()
        >>> print(final.getWinner().name)

    Example — manual step-by-step (e.g. to form coalitions between rounds):
        >>> election = Election(electionConfig=config)
        >>> round1 = election.start()
        >>> while not round1.hasWinner():
        ...     round1.formCoalition("A+B", ["A", "B"])
        ...     round1 = election.runNextIteration()
        >>> print(election.getWinner().name)
    """
    electionConfig: ElectionConfig

    _iterations: list[ElectionRound] = field(default_factory=list, init=False)

    def start(
        self,
        iterationInput: ElectionRoundInput = None,
        votes: Optional[dict] = None,
    ) -> Ballot:
        """Start the election by running the first round.

        Derives the ElectionRoundInput from electionConfig unless one is provided.
        Use run() to execute the entire election automatically or call
        runNextIteration() repeatedly for manual step-by-step control.

        Args:
            iterationInput: Optional pre-built input. If None, derived from
                electionConfig.
            votes: Optional fixed votes to inject into the first round. Passed
                to :meth:`~ipres.election_round.ElectionRoundInput.with_votes`.
                Overrides any ``vote_matrix`` already present in ``iterationInput``.

        Returns:
            The completed first Ballot.
        """
        current_input = ElectionRoundInput(
            constituencies_config=self.electionConfig.constituencies_config,
            contestants=contestantsDictFromParties(self.electionConfig.participating_parties),
            ballot_majority_percent=self.electionConfig.getBallotMajorityPercent(),
            draw_lots_strategy=self.electionConfig.draw_lots_strategy,
            rng=np.random.default_rng(self.electionConfig.seed),
            election=self
        ) if iterationInput is None else iterationInput

        if votes is not None:
            current_input = current_input.with_votes(votes)

        return Ballot.run(current_input)

    def runNextIteration(self, iterationInput: ElectionRoundInput = None) -> ElectionRound:
        """Run the next round of the election.

        Starts the election if no rounds have been run yet.
        Otherwise, continues from where the last round left off.

        Args:
            iterationInput: Optional pre-built input. If None, derived from
                the previous round's output.

        Returns:
            The completed ElectionRound.

        Example:
            >>> round1 = election.runNextIteration()
            >>> if not round1.hasWinner():
            ...     round1.formCoalition("A+B", ["A", "B"])
            ...     round1 = election.runNextIteration()
        """
        if len(self._iterations) == 0:
            return self.start(iterationInput)

        current_input = self.getLastIteration().getNextRoundInput() \
                            if iterationInput is None \
                            else iterationInput

        return ElectionRound.run(current_input)

    def run(self, on_iteration_finished: Optional[Callable[[ElectionRound], None]] = None) -> ElectionRound:
        """Run the entire election to completion.

        Executes rounds until a winner is determined. Each completed
        round is passed to on_iteration_finished if provided.

        Args:
            on_iteration_finished: Optional callback invoked after each
                round completes, including the final one.

        Returns:
            The final ElectionRound containing the winner.

        Example:
            >>> results = []
            >>> election.run(on_iteration_finished=results.append)
            >>> print(f"{len(results)} round(s), winner: {results[-1].getWinner().name}")
        """
        iteration = self.start()

        if on_iteration_finished:
            on_iteration_finished(iteration)

        while not iteration.hasWinner():
            current_input = iteration.getNextRoundInput()
            iteration = ElectionRound.run(current_input)

            if on_iteration_finished:
                on_iteration_finished(iteration)

        return iteration

    @property
    def iterations(self) -> tuple[ElectionRound, ...]:
        """Read-only view of all completed election rounds."""
        return tuple(self._iterations)

    def getNumberOfIterations(self) -> int:
        """Return the number of completed rounds."""
        return len(self._iterations)

    def getFirstIteration(self) -> ElectionRound:
        """Return the first round, or None if no rounds have been run."""
        return self._iterations[0] if len(self._iterations) > 0 else None

    def getLastIteration(self) -> ElectionRound:
        """Return the most recent round, or None if no rounds have been run."""
        return self._iterations[-1] if len(self._iterations) > 0 else None

    def _append_round(self, round: ElectionRound) -> None:
        """Append a completed round. For internal use by Ballot and DrawOfLots."""
        self._iterations.append(round)

    def hasWinner(self) -> bool:
        """Return True if the election has a winner."""
        return self.getWinner() is not None

    def isFinished(self) -> bool:
        """Return True if the election is finished (alias for hasWinner())."""
        return self.hasWinner()

    def getWinner(self) -> Contestant:
        """Return the winning Contestant, or None if the election is not finished."""
        return self._iterations[-1].getWinner() if len(self._iterations) > 0 else None

    def decisionNeededPartyReduction(self) -> bool:
        """Return whether the winner was determined through party reduction.

        True if the election required more than one round, meaning parties
        were eliminated across rounds until a winner emerged.
        """
        return self.hasWinner() and len(self._iterations[-1].getParticipatingParties()) < len(self._iterations[0].getParticipatingParties())

    def hadOutrightWinner(self) -> bool:
        """Return True if the election was won outright through a direct popular vote.

        True when the winner reached the required majority without party reduction
        across rounds or drawing of lots — i.e. in a single unforced round or
        through repeated rounds with an unchanged set of contestants.

        False when party reduction occurred or the winner was determined by lot.

        Raises:
            Exception: If the election is not yet finished.
        """
        if not self.isFinished():
            raise Exception("Election is not finished yet.")
        return not (self.decisionNeededPartyReduction() or self.getLastIteration().wasDecidedByLot())

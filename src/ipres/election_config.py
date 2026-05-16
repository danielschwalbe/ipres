from __future__ import annotations
import enum
import math
from dataclasses import field, dataclass
from enum import Enum
from typing import Optional

import numpy as np
from numpy.random import Generator

from ipres.allocation import ConstituencyAllocationMethod
from ipres.constituencies_config import ConstituenciesConfig
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit

class ConstituencyRepresentation(Enum):
    """Determines how constituencies are represented in parliament.

    - ENTIRE_PARLIAMENT: Constituencies are represented across the entire
      parliament (not exclusively by the government majority).
      Total seats = 2 * number_of_constituencies.
    - GOVERNING_MAJORITY: Constituencies are represented exclusively by the
      government majority. Size of the government majority =
      2 * number_of_constituencies. Parliament size is adjusted accordingly.
    """
    ENTIRE_PARLIAMENT = 1  # pragma: no mutate
    GOVERNING_MAJORITY = 2  # pragma: no mutate

class SeatDistributionMethod(Enum):
    """Enumeration of seat distribution methods for proportional representation.

    - SAINTE_LAGUE: Sainte-Laguë/Schepers method (used by German Bundestag).
      See `Wikipedia — Sainte-Laguë method <https://en.wikipedia.org/wiki/Sainte-Lagu%C3%AB_method>`_.
    - D_HONDT: D'Hondt method (used in many European countries).
      See `Wikipedia — D'Hondt method <https://en.wikipedia.org/wiki/D%27Hondt_method>`_.
    - HARE_NIEMEYER: Hare-Niemeyer method (largest remainder method).
      See `Wikipedia — Largest remainder method <https://en.wikipedia.org/wiki/Largest_remainder_method>`_.
    """
    SAINTE_LAGUE = "Sainte-Laguë/Schepers"  # pragma: no mutate
    D_HONDT = "d'Hondt"  # pragma: no mutate
    HARE_NIEMEYER = "Hare/Niemeyer"  # pragma: no mutate


class QuotaCorrectionStrategy(Enum):
    """Enumeration of strategies for correcting party quotas.

    When calculating party quotas as seats//2, integer division loses one quota
    for each party with odd seat count. This creates a deficit:
    sum(seats[i]//2) < sum(seats)//2

    These strategies determine which parties with odd seats receive +1 to their
    quota to ensure: sum(quotas) == number_of_constituencies

    - FAVOR_SMALL_PARTIES: Prioritize smallest parties (by seat count)
    - FAVOR_LARGE_PARTIES: Prioritize largest parties (by seat count)
    - PROPORTIONAL: Weighted random, probability proportional to seat count
    - PROPORTIONAL_REVERSED: Weighted random, probabilities reversed (small parties favored)
    - RANDOM: Uniform random selection among parties with odd seats
    - NEGOTIATED: External callback determines which parties receive +1
    """
    FAVOR_SMALL_PARTIES = "favor_small_parties"  # pragma: no mutate
    FAVOR_LARGE_PARTIES = "favor_large_parties"  # pragma: no mutate
    PROPORTIONAL = "proportional"  # pragma: no mutate
    PROPORTIONAL_REVERSED = "proportional_reversed"  # pragma: no mutate
    RANDOM = "random"  # pragma: no mutate
    NEGOTIATED = "negotiated"  # pragma: no mutate


class Language(Enum):
    """Language used for display output (table captions, column headers, chart titles).

    - DE: German (default — preserves backward compatibility)
    - EN: English
    """
    DE = "de"  # pragma: no mutate
    EN = "en"  # pragma: no mutate


from ipres.election_round import DrawLotsStrategy  # re-exported for backward compatibility

@dataclass(frozen=True)
class ElectionConfig:
    """Immutable configuration for an election simulation.

    Defines all parameters needed to run an election: constituencies,
    participating parties, the government majority threshold, tie-breaking
    strategy, and an optional random seed.

    The total number of parliamentary seats is derived automatically from
    the number of constituencies and the chosen constituency representation mode.

    Attributes:
        constituencies_config: Electoral district definitions (names, sizes,
            turnout rates).
        participating_parties: Names of parties competing in the election.
        parliament_majority_margin: How many percentage points (or seats)
            above 50% the winning coalition must hold in parliament for stable
            governance. Defaults to 5% (i.e., a 55% seat threshold).
        ballot_majority_margin: How many percentage points above 50% a
            contestant must receive in a single election round to be declared
            the winner of that round. Defaults to 2% (i.e., a 52% threshold).
        draw_lots_strategy: How to break ties during seat allocation.
            Defaults to RANDOM.
        seed: Optional integer seed for the random number generator.
            Use for reproducible simulations.
        constituency_representation: Controls how constituency seats are
            distributed. Defaults to ENTIRE_PARLIAMENT (proportional across
            all parties). Use GOVERNING_MAJORITY to assign all constituency
            seats to the winning party or coalition.
        language: Controls the display language for tables and charts. Use
            ``Language.DE`` (default) for German output or ``Language.EN``
            for English. Affects column headers, captions, chart titles, and
            number formatting in all visualization and tabulation methods.
        seat_distribution_method: Default apportionment method used by
            :class:`~ipres.seat_distributor.SeatDistributor` and
            :class:`~ipres.election_evaluator.ElectionEvaluator` when no
            override is provided (default: ``SAINTE_LAGUE``).
        quota_correction_strategy: Default quota-correction strategy used by
            :class:`~ipres.constituency_count_determiner.ConstituencyCountDeterminer`
            and :class:`~ipres.election_evaluator.ElectionEvaluator` when no
            override is provided (default: ``FAVOR_LARGE_PARTIES``).
        constituency_allocation_method: Default constituency-assignment algorithm
            used by :class:`~ipres.constituency_assigner.ConstituencyAssigner` and
            :class:`~ipres.election_evaluator.ElectionEvaluator` when no override
            is provided (default: ``OPTIMAL``).

    Example:
        >>> import pandas as pd
        >>> from ipres import ElectionConfig, ConstituenciesConfig
        >>> from ipres.election_config import ConstituencyRepresentation
        >>> from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit
        >>>
        >>> df = pd.DataFrame({"name": ["North", "South"], "size": [50000, 60000]})
        >>> cc = ConstituenciesConfig.from_dataframe(df)
        >>> config = ElectionConfig(
        ...     constituencies_config=cc,
        ...     participating_parties=["A", "B", "C"],
        ...     parliament_majority_margin=SuperMajorityMargin(10.0, MarginUnit.PERCENT),
        ...     constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY,
        ...     seed=42,
        ... )
        >>> config.parliamentarySeats
        6
        >>> config.getParliamentMajorityPercent()
        60.0
        >>> config.getParliamentMajoritySeats()
        4
    """
    # ----------------- Public Read-Only Attributes ----------------------
    constituencies_config: ConstituenciesConfig
    participating_parties: list[str]
    parliament_majority_margin: SuperMajorityMargin = field(
        default_factory=lambda: SuperMajorityMargin(5.0, MarginUnit.PERCENT)
    )
    ballot_majority_margin: SuperMajorityMargin = field(
        default_factory=lambda: SuperMajorityMargin(2.0, MarginUnit.PERCENT)
    )
    draw_lots_strategy: DrawLotsStrategy = DrawLotsStrategy.RANDOM  # pragma: no mutate
    seed: Optional[int] = None
    constituency_representation: ConstituencyRepresentation = field(
        default=ConstituencyRepresentation.ENTIRE_PARLIAMENT,
        init=True,
    )
    language: Language = Language.DE
    seat_distribution_method: SeatDistributionMethod = SeatDistributionMethod.SAINTE_LAGUE
    quota_correction_strategy: QuotaCorrectionStrategy = QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES
    constituency_allocation_method: ConstituencyAllocationMethod = ConstituencyAllocationMethod.OPTIMAL
    # ---------------------------------------------------------------------

    _parliamentary_seats: int = field(init=False)  # pragma: no mutate

    def __post_init__(self):
        _parliamentary_seats = self._get_parliamentary_seats(
            self.constituencies_config.getNumberOfConstituencies(),
            self.constituency_representation,
            self.parliament_majority_margin
        )
        object.__setattr__(self, '_parliamentary_seats', _parliamentary_seats)

    @property
    def parliamentarySeats(self) -> int:
        """Total number of seats in parliament.

        Computed from the number of constituencies and the constituency
        representation mode:

        - ENTIRE_PARLIAMENT: constituencies * 2
        - GOVERNING_MAJORITY: chosen so that getParliamentMajoritySeats()
          equals 2 * number_of_constituencies.
        """
        return self._parliamentary_seats

    @property
    def parliamentMajorityMarginPercent(self) -> float:
        """Parliament majority margin in percent, regardless of how it was specified.

        If the margin was specified in seats, converts using:
            margin_percent = 100.0 * margin_seats / parliamentarySeats

        Returns:
            Margin above 50% as a float (e.g., 5.0 for a 55% threshold).

        Raises:
            ValueError: If parliamentarySeats is not positive (only relevant
                when the margin was specified in seats).
        """
        if self.parliament_majority_margin.unit == MarginUnit.PERCENT:
            return self.parliament_majority_margin.value
        else:  # SEATS
            if self._parliamentary_seats <= 0:  # pragma: no mutate
                raise ValueError("parliamentarySeats must be positive to compute percent")  # pragma: no mutate
            return 100.0 * self.parliament_majority_margin.value / self._parliamentary_seats

    @property
    def parliamentMajorityMarginSeats(self) -> int:
        """Parliament majority margin in seats, regardless of how it was specified.

        If the margin was specified in percent, converts using:
            margin_seats = ceil(parliamentarySeats * margin_percent / 100.0)

        Returns:
            Margin above half of all seats, rounded up.
        """
        if self.parliament_majority_margin.unit == MarginUnit.SEATS:
            return int(self.parliament_majority_margin.value)
        else:  # PERCENT
            return math.ceil(self._parliamentary_seats * (self.parliament_majority_margin.value / 100.0))

    @property
    def parliamentMajoritySpecificationUnit(self) -> MarginUnit:
        """The unit (PERCENT or SEATS) used when specifying the parliament majority margin."""
        return self.parliament_majority_margin.unit

    def getParliamentMajorityPercent(self) -> float:
        """Parliament majority threshold in percent.

        Returns:
            50.0 + parliamentMajorityMarginPercent (e.g., 55.0 for a 5% margin).
        """
        return 50.0 + self.parliamentMajorityMarginPercent

    def getParliamentMajoritySeats(self) -> int:
        """Parliament majority threshold in seats.

        Returns:
            Minimum number of seats needed for a parliament majority,
            rounded up: ceil(getParliamentMajorityPercent() * parliamentarySeats / 100).
        """
        return math.ceil(self.getParliamentMajorityPercent() * self._parliamentary_seats / 100.0)

    def getBallotMajorityPercent(self) -> float:
        """Vote-share threshold (in percent) a contestant must exceed to win a single round.

        Returns:
            50.0 + ballot margin in percent (e.g., 52.0 for a 2% margin).
        """
        margin_percent = (
            self.ballot_majority_margin.value
            if self.ballot_majority_margin.unit == MarginUnit.PERCENT
            else 100.0 * self.ballot_majority_margin.value / self._parliamentary_seats
        )
        return 50.0 + margin_percent

    @staticmethod
    def _get_parliamentary_seats(
        _number_of_constituencies: int,
        _constituency_representation: ConstituencyRepresentation,
        _margin: SuperMajorityMargin
    ) -> int:
        """Calculate the number of parliamentary seats based on constituencies and representation mode.

        For GOVERNING_MAJORITY mode, ensures that:
            getParliamentMajoritySeats() = 2 * number_of_constituencies

        This guarantees that government quota allocation works correctly:
            sum(quotas) = getParliamentMajoritySeats() // 2 = number_of_constituencies
        """
        if _constituency_representation == ConstituencyRepresentation.ENTIRE_PARLIAMENT:
            return _number_of_constituencies * 2
        else:  # GOVERNING_MAJORITY
            if _margin.unit == MarginUnit.PERCENT:
                # Start with floor of ideal value
                P = int(200 * _number_of_constituencies / (50 + _margin.value))

                # Verify and adjust to ensure ceil((50 + M) * P / 100) = 2*C
                # Note: Floating-point arithmetic can introduce tiny errors, e.g.
                # mathematically 294.0 might be computed as 294.00000000000006,
                # causing ceil() to incorrectly return 295 instead of 294.
                # This adjustment corrects for such rounding errors.
                test_result = math.ceil((50 + _margin.value) * P / 100)

                if test_result < 2 * _number_of_constituencies:
                    # Need more seats to reach target
                    P += 1
                elif test_result > 2 * _number_of_constituencies:  # pragma: no mutate
                    # Floating-point error caused ceil() to round up incorrectly
                    P -= 1  # pragma: no mutate

                return P
            else:  # SEATS
                return _number_of_constituencies * 4 - 2 * int(_margin.value)

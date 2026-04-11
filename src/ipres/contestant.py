"""Contestant and coalition representations used throughout the election simulation."""

from __future__ import annotations


class Contestant:
    """A contestant in an election, representing either a single party or a coalition.

    Contestants are immutable once created. Use the factory classmethods to
    construct instances:

    - :meth:`from_party` — create a single-party contestant
    - :meth:`as_coalition` — create a coalition from existing contestants

    To create multiple single-party contestants at once, use the module-level
    helpers :func:`contestantsFromParties` and :func:`contestantsDictFromParties`.
    """

    _PRIVATE = object()
    """Sentinel to prevent direct instantiation."""

    def __init__(
        self,
        _sentinel: object,
        name: str,
        members: dict[str, Contestant],
        member_vote_weights: dict[str, float],
    ) -> None:
        if _sentinel is not Contestant._PRIVATE:
            raise TypeError(
                "Do not instantiate Contestant directly. "
                "Use Contestant.from_party() or Contestant.as_coalition()."
            )
        self._name = name
        self._members = members
        self._member_vote_weights = member_vote_weights

    # ---- Read-only properties ----

    @property
    def name(self) -> str:
        """The display name of this contestant."""
        return self._name

    @property
    def members(self) -> dict[str, Contestant]:
        """The member contestants of this coalition, keyed by their name.

        Empty for single-party contestants.
        """
        return self._members

    @property
    def member_vote_weights(self) -> dict[str, float]:
        """The vote weight fraction of each coalition member (values sum to 1.0).

        Empty for single-party contestants. For coalitions, each key is a
        member name and the value is the share of votes that member contributed
        when the coalition was formed.
        """
        return self._member_vote_weights

    # ---- Factory classmethods ----

    @classmethod
    def from_party(cls, party_name: str) -> Contestant:
        """Create a single-party contestant.

        Args:
            party_name: The name of the party.

        Returns:
            A new single-party Contestant.
        """
        return cls(cls._PRIVATE, name=party_name, members={}, member_vote_weights={})

    @classmethod
    def as_coalition(
        cls,
        name: str,
        members: list[Contestant] | dict[str, Contestant],
        member_vote_weights: dict[str, float] | None = None,
    ) -> Contestant:
        """Create a coalition contestant from a collection of member contestants.

        Args:
            name: Display name for the coalition.
            members: The member contestants, either as a list or as a dict
                mapping member name to Contestant.
            member_vote_weights: Vote weight fraction for each member. If
                omitted, equal weights (1/n) are assigned. When provided, keys
                must match the member names and values should sum to 1.0.

        Returns:
            A new coalition Contestant.
        """
        if isinstance(members, list):
            members = {m.name: m for m in members}
        if member_vote_weights is None:
            n = len(members)
            member_vote_weights = {member_name: 1.0 / n for member_name in members}
        return cls(cls._PRIVATE, name=name, members=members, member_vote_weights=member_vote_weights)

    # ---- Instance methods ----

    def isSingleParty(self) -> bool:
        """Return True if this contestant represents a single party (no members)."""
        return len(self._members) == 0

    def isCoalition(self) -> bool:
        """Return True if this contestant is a coalition of two or more members."""
        return not self.isSingleParty()

    def getMemberList(self) -> list[Contestant]:
        """Return the list of direct member contestants.

        Returns an empty list for single-party contestants.
        """
        return list(self._members.values())

    def getMemberNames(self) -> list[str]:
        """Return the names of direct member contestants.

        Returns an empty list for single-party contestants.
        """
        return list(self._members.keys())

    def getContainedParties(self) -> list[str]:
        """Return the names of all single parties recursively contained in this contestant.

        For a single party, returns a list with just its own name. For a
        coalition, recursively traverses all members and returns the leaf
        party names.
        """
        if self.isSingleParty():
            return [self._name]
        return [party for member in self._members.values() for party in member.getContainedParties()]

    def getMemberVoteWeightsForParties(self) -> dict[str, float]:
        """Return vote weight fractions for all leaf parties in this contestant.

        For a single party, returns ``{party_name: 1.0}``. For a coalition,
        recursively multiplies member weights down to the leaf parties, so the
        returned fractions reflect each original party's share of the total
        coalition votes.

        Returns:
            A dict mapping each leaf party name to its weight fraction (0–1).
            Values sum to 1.0.
        """
        if not self.isCoalition():
            return {self._name: 1.0}

        weights = {}
        for contestant in self._members.values():
            member_weight = self._member_vote_weights[contestant.name]
            for party_name, party_weight in contestant.getMemberVoteWeightsForParties().items():
                weights[party_name] = party_weight * member_weight
        return weights

    def getMemberVoteWeight(self, member_name: str) -> float:
        """Return the vote weight fraction of a direct coalition member (0–1).

        The weight represents the share of votes that member contributed when
        the coalition was formed. For example, 0.6667 means the member
        contributed 66.67% of the coalition's votes.

        Args:
            member_name: The name of the member to look up.

        Raises:
            ValueError: If called on a single-party contestant, or if
                ``member_name`` is not a direct member of this coalition.
        """
        if not self.isCoalition():
            raise ValueError(f"'{self._name}' is not a coalition, has no member vote weights")
        if member_name not in self._member_vote_weights:
            raise ValueError(f"'{member_name}' is not a member of coalition '{self._name}'")
        return self._member_vote_weights[member_name]

    # ---- Dunder methods ----

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contestant):
            return NotImplemented
        return self._name == other._name and self._members == other._members

    def __repr__(self) -> str:
        if self.isSingleParty():
            return f"Contestant(party={self._name!r})"
        return f"Contestant(coalition={self._name!r}, members={list(self._members)!r})"


# ---- Module-level helpers for creating multiple contestants ----

def contestantsFromParties(party_names: list[str]) -> list[Contestant]:
    """Create a list of single-party contestants, one per name.

    Args:
        party_names: The party names to create contestants for.

    Returns:
        A list of single-party Contestants in the same order as ``party_names``.
    """
    return [Contestant.from_party(name) for name in party_names]


def contestantsDictFromParties(party_names: list[str]) -> dict[str, Contestant]:
    """Create a dict of single-party contestants, keyed by party name.

    Args:
        party_names: The party names to create contestants for.

    Returns:
        A dict mapping each party name to its Contestant.
    """
    return {name: Contestant.from_party(name) for name in party_names}

import pytest
from ipres import Contestant, contestantsFromParties


def test_from_party():
    """Verify that from_party creates a valid single-party contestant."""
    contestant = Contestant.from_party("Partei A")
    assert contestant.name == "Partei A"
    assert contestant.isSingleParty() is True
    assert contestant.isCoalition() is False


def test_contestants_from_parties():
    """Verify that contestantsFromParties creates one contestant per name."""
    names = ["A", "B", "C"]
    list_contestants = contestantsFromParties(names)
    assert len(list_contestants) == 3
    assert list_contestants[0].name == "A"
    assert all(isinstance(c, Contestant) for c in list_contestants)


def test_coalition_logic():
    """Verify coalition detection and member access."""
    party_a = Contestant.from_party("Partei A")
    party_b = Contestant.from_party("Partei B")
    coalition = Contestant.as_coalition(
        name="Koalition AB",
        members=[party_a, party_b],
        member_vote_weights={"Partei A": 0.6, "Partei B": 0.4},
    )

    assert coalition.isSingleParty() is False
    assert coalition.isCoalition() is True
    assert len(coalition.getMemberList()) == 2
    assert "Partei A" in coalition.getMemberNames()
    assert party_a in coalition.getMemberList()


def test_as_coalition_equal_weights_default():
    """Verify that as_coalition assigns equal weights when none are provided."""
    a = Contestant.from_party("A")
    b = Contestant.from_party("B")
    coalition = Contestant.as_coalition("AB", [a, b])

    assert coalition.getMemberVoteWeight("A") == pytest.approx(0.5)
    assert coalition.getMemberVoteWeight("B") == pytest.approx(0.5)


def test_contestant_equality():
    """Verify equality comparison for single parties and coalitions."""
    a1 = Contestant.from_party("A")
    a2 = Contestant.from_party("A")
    b = Contestant.from_party("B")

    assert a1 == a2
    assert a1 != b

    c1 = Contestant.as_coalition("Coalition", [a1, b])
    c2 = Contestant.as_coalition("Coalition", [a2, b])
    c3 = Contestant.as_coalition("Coalition", [a1])
    c4 = Contestant.as_coalition("Different Name", [a1, b])

    assert c1 == c2
    assert c1 != c3
    assert c1 != c4

    # Member insertion order must not affect equality
    c5 = Contestant.as_coalition("Coalition", {"B": b, "A": a1})
    assert c1 == c5


def test_direct_instantiation_raises():
    """Verify that direct constructor calls raise TypeError.

    Mutant #563: _PRIVATE=None — Contestant(None, ...) no longer raises.
    Mutants #565, #566: XX-prefix on the two string parts of the error message.
    Pattern matches the join point "directly. Use" between the two string literals.
    """
    with pytest.raises(TypeError, match=r"directly\. Use"):
        Contestant(None, "A", {}, {})


def test_member_vote_weight_raises_for_non_coalition():
    """getMemberVoteWeight raises ValueError for a single-party contestant.

    Mutant #591: XX-prefix on error message — anchored '^' match fails on 'XX...' prefix.
    """
    c = Contestant.from_party("Solo")
    with pytest.raises(ValueError, match=r"^'Solo' is not a coalition"):
        c.getMemberVoteWeight("Solo")


def test_member_vote_weight_raises_for_unknown_member():
    """getMemberVoteWeight raises ValueError for a name not in the coalition.

    Mutant #593: XX-prefix on error message — anchored '^' match fails on 'XX...' prefix.
    """
    a = Contestant.from_party("A")
    b = Contestant.from_party("B")
    coalition = Contestant.as_coalition("AB", [a, b])
    with pytest.raises(ValueError, match=r"^'C' is not a member"):
        coalition.getMemberVoteWeight("C")


def test_contestant_repr_single_party():
    """__repr__ for a single-party contestant matches the expected format.

    Mutant #598: XX-prefix/suffix on return value.
    """
    c = Contestant.from_party("A")
    assert repr(c) == "Contestant(party='A')"


def test_contestant_repr_coalition():
    """__repr__ for a coalition contestant matches the expected format.

    Mutant #599: XX-prefix/suffix on return value.
    """
    a = Contestant.from_party("A")
    b = Contestant.from_party("B")
    coalition = Contestant.as_coalition("AB", [a, b])
    assert repr(coalition) == "Contestant(coalition='AB', members=['A', 'B'])"

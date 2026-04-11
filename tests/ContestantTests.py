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
    """Verify that direct constructor calls raise TypeError."""
    with pytest.raises(TypeError, match="Use Contestant.from_party"):
        Contestant("not_a_sentinel", "A", {}, {})

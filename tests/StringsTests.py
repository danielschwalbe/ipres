"""Tests for the strings localisation table."""

import pytest
from ipres.strings import t, format_number
from ipres.election_config import Language


@pytest.mark.parametrize("key,expected", [
    ("col_votes",          "Stimmen"),
    ("col_percent",        "Prozent"),
    ("col_seats",          "Sitze"),
    ("col_constituency",   "Wahlkreis"),
    ("col_party",          "Partei"),
    ("col_constituencies", "Wahlkreise"),
    ("col_share",          "Anteil (%)"),
    ("label_other",        "Sonstige"),
    ("label_other_detail", "Sonstige ({value})"),
    ("label_total",        "GESAMT"),
    ("label_n_parties",    "{n} Parteien"),
    ("label_parties_seats","Parteien (Sitze)"),
    ("caption_results",    "Wahlergebnisse (gesamt: {total} Stimmen)"),
    ("caption_seats",      "Sitzverteilung"),
    ("caption_constituency_party",
     "Wahlkreiszuteilung nach Parteien"),
    ("caption_constituency_constituency",
     "Wahlkreiszuteilung nach Wahlkreisen"),
    ("caption_constituency_summary",
     "Wahlkreisverteilung - Zusammenfassung"),
    ("caption_votes_per_constituency",
     "Stimmen je Wahlkreis und Partei"),
    ("caption_relative_vote_matrix",
     "Relative Stimmenmatrix r_ij = Anteil Partei j in Wahlkreis i)"),
    ("caption_constituency_importance",
     "Wahlkreis-Wichtigkeitsmatrix (w_ij = Wichtigkeit von Wahlkreis i für Partei j)"),
    ("title_vote_dist_round",
     "Stimmenverteilung (Runde {round_number}) – gesamt: {total}"),
    ("title_vote_dist_simple",
     "Stimmenverteilung (gesamt: {total} Stimmen)"),
    ("title_seat_dist",    "Sitzverteilung"),
])
def test_de_string(key, expected):
    """Each DE string key maps to the correct German label.

    Key-mutation mutants rename the key (e.g. "col_seats" → "XXcol_seatsXX"),
    causing KeyError on lookup. Value-mutation mutants change the German text
    (e.g. "Sitze" → "XXSitzeXX"), failing the equality assertion.
    Covers mutants #101–#142.
    """
    assert t(key, Language.DE) == expected


@pytest.mark.parametrize("key,expected", [
    ("col_votes",          "Votes"),
    ("col_percent",        "Percent"),
    ("col_seats",          "Seats"),
    ("col_constituency",   "Constituency"),
    ("col_party",          "Party"),
    ("col_constituencies", "Constituencies"),
    ("col_share",          "Share (%)"),
    ("label_other",        "Other"),
    ("label_other_detail", "Other ({value})"),
    ("label_total",        "TOTAL"),
    ("label_n_parties",    "{n} parties"),
    ("label_parties_seats","Parties (seats)"),
    ("caption_results",    "Election results (total: {total} votes)"),
    ("caption_seats",      "Seat distribution"),
    ("caption_constituency_party",
     "Constituency allocation by party"),
    ("caption_constituency_constituency",
     "Constituency allocation by constituency"),
    ("caption_constituency_summary",
     "Constituency distribution – Summary"),
    ("caption_votes_per_constituency",
     "Votes per constituency and party"),
    ("caption_relative_vote_matrix",
     "Relative vote matrix r_ij = share of party j in constituency i)"),
    ("caption_constituency_importance",
     "Constituency importance matrix (w_ij = importance of constituency i for party j)"),
    ("title_vote_dist_round",
     "Vote distribution (round {round_number}) – total: {total}"),
    ("title_vote_dist_simple",
     "Vote distribution (total: {total} votes)"),
    ("title_seat_dist",    "Seat distribution"),
])
def test_en_string(key, expected):
    """Each EN string key maps to the correct English label.

    Covers mutants #143–#195 (key and value mutations in the EN section).
    """
    assert t(key, Language.EN) == expected


def test_t_formats_kwargs_when_present():
    """t() must interpolate kwargs into the template when they are provided.

    Mutants 82-83 mutate the conditional ``if kwargs`` in t(), e.g. inverting it
    so kwargs are ignored when present (returning the raw "{total} Stimmen" template)
    or format() is called even when kwargs are absent.

    With key="caption_results", lang=DE, total=1000:
      correct:  "Wahlergebnisse (gesamt: 1000 Stimmen)"
      mutant:   "Wahlergebnisse (gesamt: {total} Stimmen)"  (template, not formatted)
    """
    result = t("caption_results", Language.DE, total=1000)
    assert result == "Wahlergebnisse (gesamt: 1000 Stimmen)"


def test_t_returns_raw_template_without_kwargs():
    """t() must return the raw template string when no kwargs are given.

    Complements test_t_formats_kwargs_when_present: with the inverted condition
    mutant (``if not kwargs``), calling without kwargs would invoke format() on a
    placeholder string like "{n} Parteien", raising KeyError instead of returning
    the raw template.
    """
    result = t("label_n_parties", Language.DE)
    assert result == "{n} Parteien"


def test_format_number_de_and_en():
    """format_number must use narrow no-break space (U+202F) for DE and comma for EN.

    Mutant #116: XX-prefixes the formatted string before separator replacement.
    Mutant #118: inverts the lang check, swapping DE and EN formatting.
    Mutant #119: replaces "XX,XX" instead of "," — comma left in place for DE.
    Mutant #120: replaces comma with "XX\\u202fXX" instead of "\\u202f".
    """
    assert format_number(1_234_567, Language.DE) == "1 234 567"
    assert format_number(1_234_567, Language.EN) == "1,234,567"

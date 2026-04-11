"""Localisation strings and helpers for ipres display output.

All user-visible strings (table column headers, captions, chart titles, labels)
are stored here, keyed by :class:`~ipres.election_config.Language`. Use
:func:`t` to retrieve a translated string and :func:`format_number` to format
integers with the appropriate thousands separator.

Default language is ``Language.DE`` so that all existing call sites that do not
pass a language continue to produce German output unchanged.
"""

from __future__ import annotations

from ipres.election_config import Language

_STRINGS: dict[Language, dict[str, str]] = {
    Language.DE: {
        # Column headers
        "col_votes":          "Stimmen",
        "col_percent":        "Prozent",
        "col_seats":          "Sitze",
        "col_constituency":   "Wahlkreis",
        "col_party":          "Partei",
        "col_constituencies": "Wahlkreise",
        "col_share":          "Anteil (%)",
        # Labels
        "label_other":        "Sonstige",
        "label_other_detail": "Sonstige ({value})",
        "label_total":        "GESAMT",
        "label_n_parties":    "{n} Parteien",
        "label_parties_seats":"Parteien (Sitze)",
        # Captions / titles
        "caption_results":                   "Wahlergebnisse (gesamt: {total} Stimmen)",
        "caption_seats":                     "Sitzverteilung",
        "caption_constituency_party":        "Wahlkreiszuteilung nach Parteien",
        "caption_constituency_constituency": "Wahlkreiszuteilung nach Wahlkreisen",
        "caption_constituency_summary":      "Wahlkreisverteilung - Zusammenfassung",
        "caption_votes_per_constituency":    "Stimmen je Wahlkreis und Partei",
        "caption_relative_vote_matrix":
            "Relative Stimmenmatrix r_ij = Anteil Partei j in Wahlkreis i)",
        "caption_constituency_importance":
            "Wahlkreis-Wichtigkeitsmatrix (w_ij = Wichtigkeit von Wahlkreis i für Partei j)",
        # Chart titles
        "title_vote_dist_round":  "Stimmenverteilung (Runde {round_number}) – gesamt: {total}",
        "title_vote_dist_simple": "Stimmenverteilung (gesamt: {total} Stimmen)",
        "title_seat_dist":        "Sitzverteilung",
    },
    Language.EN: {
        "col_votes":          "Votes",
        "col_percent":        "Percent",
        "col_seats":          "Seats",
        "col_constituency":   "Constituency",
        "col_party":          "Party",
        "col_constituencies": "Constituencies",
        "col_share":          "Share (%)",
        "label_other":        "Other",
        "label_other_detail": "Other ({value})",
        "label_total":        "TOTAL",
        "label_n_parties":    "{n} parties",
        "label_parties_seats":"Parties (seats)",
        "caption_results":                   "Election results (total: {total} votes)",
        "caption_seats":                     "Seat distribution",
        "caption_constituency_party":        "Constituency allocation by party",
        "caption_constituency_constituency": "Constituency allocation by constituency",
        "caption_constituency_summary":      "Constituency distribution \u2013 Summary",
        "caption_votes_per_constituency":    "Votes per constituency and party",
        "caption_relative_vote_matrix":
            "Relative vote matrix r_ij = share of party j in constituency i)",
        "caption_constituency_importance":
            "Constituency importance matrix (w_ij = importance of constituency i for party j)",
        "title_vote_dist_round":  "Vote distribution (round {round_number}) \u2013 total: {total}",
        "title_vote_dist_simple": "Vote distribution (total: {total} votes)",
        "title_seat_dist":        "Seat distribution",
    },
}


def t(key: str, lang: Language = Language.DE, **kwargs: object) -> str:
    """Return the translated string for *key* in *lang*, formatted with *kwargs*.

    Args:
        key: String key defined in ``_STRINGS``.
        lang: Target language (default ``Language.DE``).
        **kwargs: Named placeholders forwarded to :meth:`str.format`.

    Returns:
        The translated, optionally formatted string.

    Raises:
        KeyError: If *key* is not defined for *lang*.
    """
    template = _STRINGS[lang][key]
    return template.format(**kwargs) if kwargs else template


def format_number(n: int, lang: Language = Language.DE) -> str:
    """Format an integer with the locale-appropriate thousands separator.

    German uses a narrow no-break space (U+202F); English uses a comma.

    Args:
        n: Integer to format.
        lang: Target language (default ``Language.DE``).

    Returns:
        Formatted string, e.g. ``"1\u202f234\u202f567"`` (DE) or ``"1,234,567"`` (EN).
    """
    formatted = f"{n:,}"
    if lang == Language.DE:
        return formatted.replace(",", "\u202f")  # narrow no-break space
    return formatted

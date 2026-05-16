from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
import pandas as pd

from ipres.election_config import Language
from ipres.strings import t

if TYPE_CHECKING:
    from ipres.election import Election
    from ipres.election_evaluator import ElectionEvaluator

@dataclass
class ElectionResult:
    """Result of an election evaluation.

    Contains computed seat distributions, constituency assignments, and visualization methods.
    Immutable result object that keeps references to the election and evaluator for context.
    """
    election: Election
    evaluator: ElectionEvaluator
    seats: dict[str, int]
    constituency_assignments: dict[str, str]
    party_constituency_counts: dict[str, int]
    _plotter: 'ElectionPlotter' = field(init=False, repr=False, default=None)  # pragma: no mutate

    def __post_init__(self):
        from ipres.election_plotter import ElectionPlotter
        object.__setattr__(self, '_plotter', ElectionPlotter(self))

    def getSeats(self) -> dict[str, int]:
        """Get the seat distribution as a dictionary mapping party names to seat counts."""
        return self.seats

    def _lang(self) -> Language:
        """Return the display language configured in the parent election."""
        return self.election.electionConfig.language

    def getGovernmentSeats(self) -> dict[str, int]:
        """Get the seat distribution for government parties only.

        Returns:
            Dictionary mapping government party names to their seat counts
        """
        return {
            party: seat_count for party, seat_count in self.seats.items()
            if party in self.election.getWinner().getContainedParties()
        }

    def getConstituencyPartyAssignments(self) -> dict[str, str]:
        """Get constituency assignments as a dictionary mapping constituency names to party names."""
        return self.constituency_assignments

    def get_seat_distribution_table(self):
        """Create a styled pandas DataFrame showing the seat distribution.

        Returns:
            pandas.io.formats.style.Styler: Styled DataFrame for display
        """
        lang = self._lang()
        col = t("col_seats", lang)
        df = pd.DataFrame.from_dict(self.seats, orient='index', columns=[col])
        df.sort_values(by=[col], ascending=False, inplace=True)
        style = df.style.set_caption(t("caption_seats", lang))
        return style

    def get_constituency_assignment_table(self, sort_by='party'):
        """Creates a pandas DataFrame table showing constituency-party assignments.

        Args:
            sort_by: Sort order, either 'party' (default) or 'constituency'
                - 'party': Sort by party name, then constituency name
                - 'constituency': Sort by constituency name only

        Returns:
            pandas.io.formats.style.Styler: Styled DataFrame for display
        """
        lang = self._lang()
        col_c = t("col_constituency", lang)
        col_p = t("col_party", lang)
        assignments = self.constituency_assignments

        # Create DataFrame with constituency -> party mapping
        df = pd.DataFrame([
            {col_c: constituency, col_p: party}
            for constituency, party in assignments.items()
        ])

        # Sort according to parameter
        if sort_by == 'party':
            df = df.sort_values([col_p, col_c]).reset_index(drop=True)
        elif sort_by == 'constituency':
            df = df.sort_values(col_c).reset_index(drop=True)
        else:
            raise ValueError(f"sort_by must be 'party' or 'constituency', got '{sort_by}'")

        # Create summary
        party_counts = pd.Series(assignments.values()).value_counts()
        summary_df = pd.DataFrame([{
            col_c: t("label_total", lang),
            col_p: t("label_n_parties", lang, n=len(party_counts)),
        }])

        # Combine
        result_df = pd.concat([df, summary_df], ignore_index=True)

        # Style the table
        caption_key = "caption_constituency_party" if sort_by == 'party' else "caption_constituency_constituency"
        style = result_df.style.set_caption(t(caption_key, lang))

        return style

    def get_constituency_summary_table(self):
        """Creates a summary table showing how many constituencies each party received.

        Returns:
            pandas.io.formats.style.Styler: Styled DataFrame for display
        """
        lang = self._lang()
        col_p = t("col_party", lang)
        col_c = t("col_constituencies", lang)
        col_s = t("col_share", lang)
        assignments = self.constituency_assignments
        total_constituencies = len(assignments)

        # Count constituencies per party
        party_counts = pd.Series(assignments.values()).value_counts()

        # Create DataFrame
        df = pd.DataFrame({
            col_p: party_counts.index,
            col_c: party_counts.values,
            col_s: (party_counts.values / total_constituencies * 100).round(1),
        })

        # Sort by number of constituencies descending
        df = df.sort_values(col_c, ascending=False).reset_index(drop=True)

        # Add total row
        total_row = pd.DataFrame([{
            col_p: t("label_total", lang),
            col_c: total_constituencies,
            col_s: 100.0,
        }])

        result_df = pd.concat([df, total_row], ignore_index=True)

        # Style the table
        style = result_df.style.set_caption(t("caption_constituency_summary", lang))

        return style

    def plot_seat_share_pie(self, title: Optional[str] = None, group_coalitions: bool = True, min_seats_for_display: int = 5):  # pragma: no mutate
        """Visualisiert die Stimmenverteilung dieser Iteration als Tortendiagramm.

        Args:
            title: Titel des Diagramms
            group_coalitions: Wenn True, werden Koalitionsmitglieder nebeneinander platziert
                             und mit ähnlichen Farben dargestellt
            min_seats_for_display: Mindestanzahl Sitze für separate Darstellung im Diagramm.
                                  Parteien mit weniger Sitzen werden unter "Sonstige" gruppiert.

        Returns:
            matplotlib.figure.Figure
        """
        return self._plotter.plot_seat_share_pie(title, group_coalitions, min_seats_for_display)

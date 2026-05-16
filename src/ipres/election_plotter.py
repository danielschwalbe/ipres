"""Election result visualisation helpers."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import numpy as np
import matplotlib.pyplot as plt

from ipres.strings import t

if TYPE_CHECKING:
    from ipres.election_result import ElectionResult

class ElectionPlotter:
    """Helper class for plotting election results.

    Separates visualization logic from the main ElectionResult class.
    """

    def __init__(self, result: ElectionResult):
        self.result = result

    def plot_seat_share_pie(self, title: Optional[str] = None, group_coalitions: bool = True, min_seats_for_display: int = 5):
        """Visualise the seat distribution of this election result as a pie chart.

        Args:
            title: Chart title. Defaults to a generated label when ``None``.
            group_coalitions: If ``True``, coalition members are placed adjacent
                to each other and rendered with similar colours.
            min_seats_for_display: Minimum number of seats required for a party
                to appear individually in the chart. Parties below this threshold
                are grouped under "Sonstige" (other).

        Returns:
            :class:`matplotlib.figure.Figure`
        """
        lang = self.result.election.electionConfig.language
        label_other = t("label_other", lang)
        label_other_detail = lambda v: t("label_other_detail", lang, value=v)
        label_parties_seats = t("label_parties_seats", lang)
        label_seat_dist = t("title_seat_dist", lang)
        seats = self.result.getSeats()

        # Hole Contestants um Koalitionen zu erkennen
        contestants = {}
        if self.result.election.getLastIteration():
            contestants = self.result.election.getLastIteration().getContestants()

        # filter out all contestants that do not have a seat
        seats = {name: count for name, count in seats.items() if count > 0}
        contestants = {name : contestant for name, contestant in contestants.items() for p in contestant.getContainedParties() if p in seats.keys()}

        # Ordne Parteien so an, dass Koalitionsmitglieder nebeneinander sind
        labels = []
        values = []
        colors = []
        processed = set()
        party_to_coalition = {}  # Mapping: Partei -> Koalitionsname (falls Teil einer Koalition)
        small_parties = []  # Liste kleiner Parteien für "Sonstige"-Gruppierung: [(name, seats), ...]

        # Basis-Farbpalette für Parteien
        base_colors = plt.cm.Set3(np.linspace(0, 1, 12))  # pragma: no mutate
        color_idx = 0

        if group_coalitions and contestants:
            # Erstelle Mapping: welche Partei gehört zu welcher Koalition?
            for coalition_name, contestant in contestants.items():
                if contestant.isCoalition():
                    for party_name in contestant.getContainedParties():
                        party_to_coalition[party_name] = coalition_name

            # Gruppiere Parteien nach Koalitionen
            coalitions_added = set()

            # Berechne Gesamtsitze pro Koalition
            coalition_total_seats = {}
            for coalition_name, contestant in contestants.items():
                if contestant.isCoalition():
                    total = sum(seats.get(p, 0) for p in contestant.getContainedParties())
                    if total > 0:  # pragma: no mutate
                        coalition_total_seats[coalition_name] = total

            # Sortiere Koalitionen nach Gesamtsitzen (absteigend)
            sorted_coalitions = sorted(coalition_total_seats.items(),
                                      key=lambda x: x[1], reverse=True)

            # Zuerst alle Koalitionen mit ihren Mitgliedern hinzufügen (nach Größe sortiert)
            for coalition_name, total_seats in sorted_coalitions:
                if coalition_name not in coalitions_added:
                    coalitions_added.add(coalition_name)

                    # Wähle eine Basisfarbe für diese Koalition
                    base_color = base_colors[color_idx % len(base_colors)]
                    color_idx += 1  # pragma: no mutate

                    # Finde alle Mitglieder dieser Koalition die Sitze haben und sortiere nach Sitzanzahl
                    coalition_members = [(p, seats[p]) for p in seats.keys()
                                       if party_to_coalition.get(p) == coalition_name]
                    coalition_members.sort(key=lambda x: x[1], reverse=True)
                    member_count = len(coalition_members)

                    # Füge alle Mitglieder nacheinander hinzu (nach Sitzanzahl sortiert)
                    for i, (member_name, seat_count) in enumerate(coalition_members):
                        if member_name not in processed:
                            labels.append(member_name)
                            values.append(seat_count)

                            # Erstelle Farbvariante: von hell (0.6) bis dunkel (1.0)
                            brightness = 0.6 + 0.4 * (i / max(member_count - 1, 1))  # pragma: no mutate
                            color_variant = base_color * brightness
                            color_variant[3] = 1.0  # Alpha = 1 (nicht transparent)
                            colors.append(color_variant)

                            processed.add(member_name)

            # Dann alle übrigen Parteien hinzufügen (nach Sitzanzahl sortiert)
            non_coalition_parties = [(p, seats[p]) for p in seats.keys()
                                    if p not in processed]
            non_coalition_parties.sort(key=lambda x: x[1], reverse=True)

            # Trenne große Parteien (≥ Schwellenwert) von kleinen Parteien (< Schwellenwert)
            large_parties = [(p, s) for p, s in non_coalition_parties if s >= min_seats_for_display]
            small_parties = [(p, s) for p, s in non_coalition_parties if s < min_seats_for_display]

            # Füge große Parteien einzeln hinzu
            for party_name, seat_count in large_parties:
                labels.append(party_name)
                values.append(seat_count)
                colors.append(base_colors[color_idx % len(base_colors)])
                color_idx += 1
                processed.add(party_name)

            # Füge "Sonstige" als ein Segment hinzu (wenn es kleine Parteien gibt)
            if small_parties:
                total_small_seats = sum(s for _, s in small_parties)
                labels.append(label_other)
                values.append(total_small_seats)
                colors.append(plt.cm.Greys(0.5))  # Graue Farbe für Sonstige
                # processed wird für kleine Parteien nicht aktualisiert, da sie nicht einzeln im Diagramm sind
        else:
            # Keine Gruppierung, einfach wie im seats dict
            labels = list(seats.keys())
            values = list(seats.values())
            colors = [base_colors[i % len(base_colors)] for i in range(len(labels))]

        fig, ax = plt.subplots(figsize=(8, 10))

        # Verwende Iterator um tatsächliche Sitzzahlen anzuzeigen (keine Rundungsfehler)
        def make_autopct(values):
            """Return an autopct formatter that displays actual seat counts instead of percentages."""
            # Iterator über die tatsächlichen Werte
            value_iter = iter(values)
            def my_autopct(pct):
                # Gib den nächsten tatsächlichen Wert zurück
                return f'{next(value_iter)}'
            return my_autopct

        # Zeichne Tortendiagramm mit benutzerdefinierten Farben
        # Keine Kanten zwischen Segmenten (linewidth=0), wir zeichnen sie später selektiv
        # Verwende keine labels im pie() selbst, sondern eine Legende um Überlappungen zu vermeiden
        wedges, _, _ = ax.pie(values, labels=labels, autopct=make_autopct(values),
                startangle=90, counterclock=False, colors=colors, radius=1.2,  # pragma: no mutate
                wedgeprops={'linewidth': 0, 'edgecolor': 'none'})

        # Füge Legende hinzu (unterhalb des Diagramms, mehrspaltig)
        # Custom Legend: Erweitere "Sonstige" mit einzelnen Parteien
        legend_handles = []
        legend_labels_extended = []

        for i, (label, value) in enumerate(zip(labels, values)):
            if label == label_other:
                # Für "Sonstige": Zeige Summe und dann alle Einzelparteien eingerückt
                legend_handles.append(wedges[i])
                legend_labels_extended.append(label_other_detail(value))

                # Füge alle kleinen Parteien eingerückt hinzu
                for small_party, small_seats in small_parties:
                    # Erstelle Handle mit gleicher Farbe wie "Sonstige"
                    legend_handles.append(plt.Rectangle((0,0),1,1, fc=colors[i], ec='none', alpha=0.7))  # pragma: no mutate
                    legend_labels_extended.append(f"  • {small_party} ({small_seats})")
            else:
                legend_handles.append(wedges[i])
                legend_labels_extended.append(f"{label} ({value})")

        ax.legend(legend_handles, legend_labels_extended, title=label_parties_seats, loc="upper center",
                  bbox_to_anchor=(0.5, -0.05), fontsize=9, ncol=4, frameon=False)  # pragma: no mutate

        # Zeichne Trennlinien zwischen Segmenten (nur zwischen Koalitionen)
        if group_coalitions and contestants and party_to_coalition:
            # Berechne Winkel für jedes Segment
            total = sum(values)
            current_angle = 90  # startangle in Grad
            radius = 1.2  # muss mit dem radius in ax.pie() übereinstimmen

            for i in range(len(labels)):
                # Winkel des aktuellen Segments
                segment_angle = (values[i] / total) * 360

                # Prüfe Trennlinie zur nächsten Partei (zyklisch, d.h. letzte zu erster)
                label = labels[i]
                next_label = labels[(i + 1) % len(labels)]

                # Prüfe ob beide zur gleichen Koalition gehören
                label_coalition = party_to_coalition.get(label)
                next_coalition = party_to_coalition.get(next_label)  # pragma: no mutate

                # Berechne Endwinkel des aktuellen Segments (Grenze zum nächsten)
                boundary_angle = current_angle - segment_angle

                # Zeichne Trennlinie an Koalitionsgrenzen
                # Linie wird gezeichnet wenn mindestens eine Partei in einer Koalition ist
                # UND sie zu verschiedenen Koalitionen gehören (oder eine nicht in einer Koalition ist)
                if ((label_coalition is not None or next_coalition is not None) and
                    label_coalition != next_coalition):
                    # Koalitionsgrenze: dicke schwarze Linie bis zum Rand
                    angle_rad = np.radians(boundary_angle)
                    ax.plot([0, radius * np.cos(angle_rad)],  # pragma: no mutate
                           [0, radius * np.sin(angle_rad)],
                           color='black', linewidth=2.5, zorder=10, solid_capstyle='butt')

                current_angle -= segment_angle

        ax.axis('equal')
        ax.set_title(title if title is not None else label_seat_dist)
        return fig

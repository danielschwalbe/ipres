# Wahlkreisanzahlzuordnung

Nach der Mandatszuteilung wird festgelegt, wie viele Wahlkreise jeder Partei zugeteilt werden. Das Grundprinzip: Die Hälfte der einer Partei zustehenden Sitze wird über Direktmandate in Wahlkreisen besetzt – also durch den Bürger gewählt. Die andere Hälfte vergibt die Partei selbst. So wird einerseits demokratische Kontrolle durch den Bürger sichergestellt – man kennt seinen Abgeordneten persönlich –, andererseits können Parteien gezielt Fachleute ins Parlament entsenden, die nicht zwingend bürgernah auftreten müssen.

**Grundformel:** `Wahlkreisanzahl(Partei) = Parlamentssitze(Partei) // 2`

---

## Das Ganzzahlproblem

Die ganzzahlige Division durch 2 erzeugt ein strukturelles Problem: Parteien mit einer **ungeraden** Sitzzahl verlieren durch das Abrunden jeweils ein halbes Wahlkreisrecht. Das führt dazu, dass die Summe der Grundzuteilungen kleiner sein kann als die Gesamtzahl der Wahlkreise:

```
sum(sitze_i // 2)  <  sum(sitze_i) // 2
```

**Beispiel** (7 Wahlkreise, 14 Parlamentssitze):

| Partei | Sitze | Grundzuteilung (`// 2`) |
|--------|-------|-------------------|
| A      | 10    | 5                 |
| B      | 3     | 1                 |
| C      | 1     | 0                 |
| **Σ**  | 14    | **6** ← Defizit 1 |

Die Summe der Grundzuteilungen ergibt 6, obwohl 7 Wahlkreise vergeben werden müssen. Die Korrektur gibt das fehlende +1 an eine der Parteien mit ungerader Sitzzahl (hier B oder C).

---

## Korrekturstrategie

Das fehlende +1 (oder mehrere, falls mehrere Parteien betroffen sind) wird nach einer konfigurierbaren Strategie vergeben. Nur Parteien mit **ungerader** Sitzzahl kommen als Empfänger in Frage, da nur bei ihnen eine Korrektur mathematisch vertretbar ist.

| Strategie | Beschreibung |
|---|---|
| `FAVOR_LARGE_PARTIES` *(Standard)* | Die Partei(en) mit den meisten Sitzen erhalten das +1. |
| `FAVOR_SMALL_PARTIES` | Die Partei(en) mit den wenigsten Sitzen erhalten das +1. |
| `PROPORTIONAL` | Zufällig, gewichtet nach Sitzzahl (größere Parteien wahrscheinlicher). |
| `PROPORTIONAL_REVERSED` | Zufällig, umgekehrt gewichtet (kleinere Parteien wahrscheinlicher). |
| `RANDOM` | Gleichverteilte Zufallsauswahl unter den Parteien mit ungerader Sitzzahl. |
| `NEGOTIATED` | Externe Callback-Funktion entscheidet, welche Parteien das +1 erhalten. |

Im obigen Beispiel mit `FAVOR_LARGE_PARTIES`: B hat mehr Sitze als C, also erhält B das +1 → B: 2, C: 0.

**Hinweis**: Das Korrekturverfahren legt auch im Einzelfall fest, ob eine Partei mit nur einem Sitz diesen durch einen Wahlkreisvertreter besetzen darf.  

---

## Einfluss von `constituency_representation`

Dieser Parameter (aus der globalen Konfiguration) steuert, welche Parteien überhaupt Wahlkreise erhalten:

- **`ENTIRE_PARLIAMENT`** *(Standard)*: Alle Parteien erhalten Wahlkreise proportional zu ihren Sitzen.
- **`GOVERNING_MAJORITY`**: Nur die Regierungsparteien erhalten Wahlkreise. Die Opposition erhält 0 Wahlkreise.

---

## Konfigurationsparameter

| Parameter | Klasse | Beschreibung |
|---|---|---|
| `quota_correction_strategy` | `ElectionEvaluator` | Korrekturstrategie (Standard: `FAVOR_LARGE_PARTIES`) |
| `constituency_representation` | `ElectionConfig` + `ElectionEvaluator` | Wer erhält Wahlkreise? |

---

## Ausführung in der Simulation

Die Klasse [`ConstituencyCountDeterminer`](../../src/ipres/constituency_count_determiner.py) führt diesen Schritt durch. Sie nimmt das Ergebnis der Mandatszuteilung als Eingabe entgegen.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, ConstituencyCountDeterminer,
                   SuperMajorityMargin, MarginUnit)
import pandas as pd

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['WK1', 'WK2', 'WK3', 'WK4', 'WK5'],
    'constituency_size': [100_000] * 5,
}))
config = ElectionConfig(
    constituencies_config=cc,
    participating_parties=['A', 'B', 'C'],
    parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
)

election = Election(electionConfig=config)
votes = {wk: {'A': 60, 'B': 25, 'C': 15} for wk in ['WK1', 'WK2', 'WK3', 'WK4', 'WK5']}
election.start(votes=votes)

sitze = SeatDistributor().run(election)               # {'A': 6, 'B': 2, 'C': 2}
anzahl = ConstituencyCountDeterminer().run(election, sitze)
print(anzahl)  # {'A': 3, 'B': 1, 'C': 1}
```
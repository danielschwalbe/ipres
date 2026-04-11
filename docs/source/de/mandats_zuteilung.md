# Mandatszuteilung

Nach Abschluss der iterativen Verhältniswahl werden die Parlamentssitze auf die Parteien verteilt. Das Verfahren unterscheidet zwei Fälle.

---

## Fall 1 — Gewinner erhält zugewiesene Mehrheit

**Bedingung:** Die Gewinnerpartei (oder -koalition) hat die Parlamentsmehrheitsschwelle *nicht* durch direktes Überschreiten im letzten Wahlgang erreicht. Das ist der Fall, wenn:

- der Gewinner durch Parteiausscheidung über mehrere Runden oder durch Losentscheid festgestellt wurde, **oder**
- der Gewinner den Wahlgangschwellenwert (z. B. 52 %) zwar übertroffen hat, aber unter der Parlamentsmehrheitsschwelle (z. B. 55 %) liegt.

**Vorgehen:**

1. Der Gewinner erhält genau so viele Sitze, wie zur Parlamentsmehrheit erforderlich sind (abfragbar über `ElectionConfig.getParliamentMajoritySeats()`).
2. Die verbleibenden Sitze werden proportional auf die **übrigen Parteien** verteilt – anteilig nach deren Stimmanteil im **ersten Wahlgang** (vor jeder Koalitionsbildung oder Parteiausscheidung).

Das Ergebnis des ersten Wahlgangs wird deshalb herangezogen, weil es am unmittelbarsten dem Wählerwillen entspricht: Alle Parteien traten noch an, und kein Wähler musste taktisch abstimmen.

---

## Fall 2 — Proportionale Verteilung aller Sitze

**Bedingung:** Der Gewinner hat die Parlamentsmehrheitsschwelle durch einen eindeutigen Sieg im letzten Wahlgang übertroffen.

**Vorgehen:** Alle Parlamentssitze werden proportional nach dem Ergebnis des **letzten Wahlgangs** verteilt. Dabei werden Koalitionsstimmen zusammengezählt.

---

## Koalitionen

Hat eine Koalition Sitze gewonnen, werden diese nach der Gesamtzuteilung proportional auf die Koalitionsmitglieder aufgeteilt. Als Gewichte dienen die Stimmgewichte der Mitgliedsparteien aus dem Wahlgang, in dem die Koalition gebildet wurde.

---

## Sitzverteilungsmethode

Sitze sind unteilbar. Eine rein proportionale Rechnung ergibt in der Regel gebrochene Zahlen (z. B. „Partei A verdient 12,7 Sitze"), die auf ganze Zahlen gerundet werden müssen, ohne dass die Gesamtsumme verändert wird. Verschiedene Rundungsverfahren behandeln diese Nachkommastellen unterschiedlich und bevorzugen dabei tendenziell entweder größere oder kleinere Parteien. Ein solches Verfahren wird Zuteilungsverfahren genannt.

Für die proportionale Aufteilung (sowohl der Gesamtsitze als auch innerhalb von Koalitionen) wird ein Zuteilungsverfahren verwendet. Die Methode wird über den Parameter `seat_distribution_method` in [`ElectionEvaluator`](../../../src/ipres/election_evaluator.py) konfiguriert. Zur Auswahl stehen:

| Methode | Beschreibung |
|---|---|
| `SAINTE_LAGUE` *(Standard)* | Sainte-Laguë/Schepers-Verfahren, auch als Webster-Verfahren bekannt. Wird beim deutschen Bundestag verwendet. Bevorzugt weder große noch kleine Parteien. |
| `D_HONDT` | D'Hondt-Verfahren (höchste Durchschnittswerte). Wird in vielen europäischen Ländern eingesetzt. Begünstigt leicht größere Parteien. |
| `HARE_NIEMEYER` | Hare-Niemeyer-Verfahren (größte Reste). Teilt Sitze zunächst nach dem ganzzahligen Anteil zu und vergibt Restsitze nach dem größten Rest. |

Details und Verlinkung auf weiterführende Quellen: siehe [`SeatDistributionMethod`](globale_konfiguration.md) in der globalen Konfiguration.

---

## Konfigurationsparameter

| Parameter | Klasse | Beschreibung |
|---|---|---|
| `seat_distribution_method` | `ElectionEvaluator` | Zuteilungsverfahren (Standard: `SAINTE_LAGUE`) |
| `parliament_majority_margin` | `ElectionConfig` | Regierungsabstand – bestimmt den Rückgabewert von `getParliamentMajoritySeats()` |

---

## Ausführung in der Simulation

Die Klasse [`SeatDistributor`](../../src/ipres/seat_distributor.py) führt die Mandatszuteilung durch. Sie kann direkt aufgerufen oder implizit über `ElectionEvaluator.evaluate()` genutzt werden.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, SuperMajorityMargin, MarginUnit)
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

# A gewinnt mit 60 % > Parlamentsschwelle 55 % → Fall 2: proportionale Verteilung
election = Election(electionConfig=config)
votes = {wk: {'A': 60, 'B': 25, 'C': 15} for wk in ['WK1', 'WK2', 'WK3', 'WK4', 'WK5']}
election.start(votes=votes)

sitze = SeatDistributor().run(election)
print(sitze)  # {'A': 6, 'B': 2, 'C': 2}
```
# Iteratives Verhältniswahlrecht mit garantiertem Gewinner
## Verfahrensbeschreibung

Das Kernstück des Verfahrens ist ein iterativer Wahlprozess, der sicherstellt, dass am Ende immer eine Partei oder Koalition mit klarer Regierungsmehrheit hervorgeht – ohne dass dafür eine erzwungene Koalition nötig ist.
Im Gegensatz zu den klassischen Mehrheitswahlverfahren, die durch Nichtlinearität auch Gewinner produzieren, sind die Stimmen der Verlierer bis zur letzen Iteration nicht verloren. Auch die, deren Partei ausgeschieden ist, dürfen erneut über die reduzierte Parteienliste abstimmen und ggf. nach dem Prinzip "des kleineren" Übels ihre Stimme einer anderen Partei, die noch im Rennen ist, geben.

### Schritt 1: Erste Verhältniswahl

Es wird eine normale Verhältniswahl durchgeführt. Die Parteien werden nach ihrem prozentualen Stimmanteil geordnet.

- **Gibt es einen Gewinner?** Eine Partei oder eine freiwillig gebildete Koalition erreicht die absolute Mehrheit (ein vorab festgelegter Prozentsatz knapp über 50 %, so dass die Regierung auch bei Abwesenheit einzelner Abgeordneter handlungsfähig bleibt) → **Verfahren beendet.**
- **Kein Gewinner?** → Weiter mit Schritt 2.

### Schritt 2: Reduktion und erneuter Wahlgang

Die Stimmenanteile werden beginnend mit der stärksten Partei kumuliert, bis **zwei Drittel** aller Stimmen erreicht oder überschritten sind. Nur die Parteien, die in dieser Summe enthalten sind, nehmen am nächsten Wahlgang teil. Alle Wähler – auch jene, deren Partei ausgeschieden ist – dürfen erneut abstimmen.

Das Verfahren kehrt zu Schritt 1 zurück.

### Sonderfall: Nur noch zwei Parteien

- **Erster Durchgang mit zwei Parteien:** Wahlgang wird wiederholt.
- **Zweiter ergebnisloser Durchgang:** Ein Zufallsverfahren entscheidet (z. B. minimale prozentuale Unterschiede oder das Los).

### Terminierung

Das Verfahren terminiert garantiert, weil sich die Anzahl der antretenden Parteien in jeder Iteration reduziert, bis schließlich nur noch zwei übrig sind.

### Beispiel (drei Wahlgänge)

| Partei | Wahlgang 1 | Wahlgang 2 | Wahlgang 3 |
|--------|-----------|-----------|-----------|
| A      | 28 %      | 35 %      | 52 % ✓   |
| B      | 25 %      | 33 %      | 48 %      |
| C      | 20 %      | 32 %      | –         |
| D      | 15 %      | –         | –         |
| E      | 12 %      | –         | –         |

*Nach Wahlgang 1:* A+B+C summieren sich auf 73 % ≥ 2/3 → D und E scheiden aus.
*Nach Wahlgang 2:* A+B summieren sich auf 68 % ≥ 2/3 → C scheidet aus.
*Wahlgang 3:* A erreicht 52 % → **A gewinnt.**

## Ausführung in der Simulation

In der Simulation wird eine Wahl gestartet, indem ein {class}`~ipres.election.Election`-Objekt erzeugt wird. Der Konstruktor erwartet ein {class}`~ipres.election_config.ElectionConfig`-Objekt mit der im ersten Schritt erstellten globalen Verfahrenskonfiguration.

Mithilfe der {meth}`Election.run() <ipres.election.Election.run>` oder der {meth}`Election.start() <ipres.election.Election.start>` Methode wird das Verfahren gestartet. Die {meth}`Election.run() <ipres.election.Election.run>` Methode führt das gesamte Verfahren aus, während die {meth}`Election.start() <ipres.election.Election.start>` Methode nur den ersten Durchgang ausführt und eine Referenz auf den ausgeführten Durchgang zurückgibt. Das erlaubt es, interaktiv in den Wahlprozess einzugreifen, um z. B. Koalitionen zu bilden oder die Wirkung einzelner Parameter zu testen.

**Automatischer Ablauf**:

```python
election = Election(electionConfig=config)
final_round = election.run()
print(final_round.getWinner().name)
```


Ein Durchgang wird durch eine Instanz der {class}`~ipres.election_round.ElectionRound`-Klasse dargestellt. Die {class}`~ipres.election_round.ElectionRound`-Klasse weiß, ob noch ein nächster Wahlgang erforderlich ist oder nicht. Wenn ja, gibt sie den Input für die nächste Runde zurück. Dieser kann ggf. manuell überschrieben werden, um gezielt bestimmte Anwendungsfälle zu testen. 

Ein Wahldurchgang wird ausgeführt, indem {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>` aufgerufen wird. ({meth}`Election.start() <ipres.election.Election.start>` ruft intern auch {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>` auf.)  Die Klassenmethode {meth}`ElectionRound.run() <ipres.election_round.ElectionRound.run>` nimmt ein {class}`~ipres.election_round.ElectionRoundInput`-Objekt als Parameter und gibt ein {class}`~ipres.election_round.ElectionRound`-Objekt mit dem Ergebnis des ausgeführten Wahldurchgangs zurück. Je nachdem, ob es sich um einen echten Wahlgang oder einen Losentscheid gehandelt hat, ist das Ergebnis eine Instanz von {class}`~ipres.ballot.Ballot` oder {class}`~ipres.draw_of_lots.DrawOfLots`. Beide Klassen sind Unterklassen von {class}`~ipres.election_round.ElectionRound`. 

Das Verfahren ist erst beendet, wenn es einen Gewinner gibt. In diesem Fall gibt {meth}`ElectionRound.hasNext() <ipres.election_round.ElectionRound.hasNext>` `False` zurück und {meth}`ElectionRound.hasWinner() <ipres.election_round.ElectionRound.hasWinner>` ist `True`.
Erst dann kann die Wahl ausgewertet werden.

Durch Bildung von Koalitionen kann ein Durchgang, der eigentlich ohne Gewinner ausgegangen ist, doch nachträglich einen Gewinner erhalten. Koalitionen werden durch Aufruf von {meth}`Ballot.formCoalition() <ipres.ballot.Ballot.formCoalition>` erstellt. Man beachte, dass Koalitionen erst nach einem Wahlgang gebildet werden können und einmal zusammengeschlossen, bis zum Ende des Verfahrens zusammenbleiben müssen, damit sichergestellt ist, dass sich in jeder Runde die Anzahl der Teilnehmer reduziert.

Details zu `Contestant` und Koalitionsbildung zeigt das Notebook [Wahlteilnehmer](../../notebooks/de/wahlteilnehmer.ipynb).

**Manueller Ablauf mit Koalitionsbildung:**

```python
election = Election(electionConfig=config)
round1 = election.start()

if not round1.hasWinner():
    round1.formCoalition("A+B", ["A", "B"])

while not election.hasWinner():
    election.runNextIteration()

print(election.getWinner().name)
```

### Stimmeninjektion

Standardmäßig generiert die Simulation Stimmen zufällig auf Basis von Wahrscheinlichkeiten und Wahlbeteiligung aus der Konfiguration. Für Tests, Demonstrationen oder die Analyse konkreter Szenarien können Stimmen auch fest vorgegeben werden.

Für den ersten Wahlgang nimmt {meth}`Election.start() <ipres.election.Election.start>` einen optionalen `votes`-Parameter entgegen:

```python
runde1 = election.start(votes={'A': 28, 'B': 25, 'C': 20, 'D': 15, 'E': 12})
```

Für Folgerunden steht die Methode {meth}`ElectionRoundInput.with_votes() <ipres.election_round.ElectionRoundInput.with_votes>` auf dem von {meth}`ElectionRound.getNextRoundInput() <ipres.election_round.ElectionRound.getNextRoundInput>` zurückgegebenen Input zur Verfügung:

```python
runde2 = election.runNextIteration(
    iterationInput=runde1.getNextRoundInput().with_votes({'A': 35, 'B': 33, 'C': 32})
)
```

`getNextRoundInput()` liefert den vorbereiteten Input für die nächste Runde – mit allen übernommenen Einstellungen (verbliebene Teilnehmer, Schwellenwert, Strategie usw.), aber ohne Stimmen. `with_votes()` ergänzt diesen Input um die gewünschten Stimmzahlen und gibt eine neue Kopie des Inputs mit den vorgegebenen Stimmzahlen zurück.

Bei mehreren Wahlkreisen wird ein verschachteltes Dict übergeben:

```python
runde1.getNextRoundInput().with_votes({
    'WK1': {'A': 35, 'B': 33, 'C': 32},
    'WK2': {'A': 40, 'B': 30, 'C': 30},
})
```
### Relevante Konfigurationsparameter

#### `ballot_majority_margin` — Wahlgangschwelle

Mit `ballot_majority_margin` wird gesteuert, ab welchem Stimmenanteil ein einzelner Wahlgang einen Gewinner ergibt (Standard: 2 % über 50 % = 52 %). Sie ist unabhängig von der `parliament_majority_margin`. Die Angabe ist in Prozent (`MarginUnit.PERCENT`) oder in Sitzen (`MarginUnit.SEATS`) möglich.

#### `DrawLotsStrategy` — Losstrategie

Wenn zwei Parteien in zwei aufeinanderfolgenden Wahlgängen keinen Gewinner produzieren, entscheidet im dritten Durchgang das Los:

- **`DrawLotsStrategy.RANDOM`** *(Standard)*: gleichverteiltes Zufallsverfahren.
- **`DrawLotsStrategy.MARGINAL_LEAD`**: Der marginale Stimmunterschied gilt als zufällig entstanden — die Partei, die zufällig etwas mehr Stimmen erhalten hat, gewinnt.

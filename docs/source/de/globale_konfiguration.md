# Wahlkonfiguration

## Erklärung der wichtigsten Verfahrensparameter
Das Wahlverfahren hängt von einigen Parametern ab, von denen die folgenden drei die wichtigsten sind:
- Anzahl der Wahlkreise
- Wahlkreisrepräsentation: **Gesamtes Parlament** oder **Regierungsmehrheit**
- Regierungsmehrheit

Durch diese drei Parameter wird die Größe des Parlaments festgelegt.

Jeder Wahlkreis soll einen Repräsentanten im Parlament haben. Aus der Sicht eines Wahlkreises kann es dabei schon einen Unterschied machen, ob sein Repräsentant in der Regierungsfraktion sitzt oder nicht. Man könnte deshalb verlangen, dass jeder Wahlkreis einen Repräsentanten in der Regierungsfraktion hat. Da wir aber gleichzeitig allen Parteien das Recht zugestehen wollen, genauso viele eigene Kandidaten ins Parlament einzubringen, wie der Wähler direkt gewählt hat, ergeben sich dadurch große Parlamente.

Anzahl der Wahlkreise * 2 = Anzahl der Regierungssitze = ceil(Regierungsmehrheit in % / 100 * Anzahl der Parlamentssitze) <br>
Parlamentssitze ≈ int(200 * Anzahl Wahlkreise / Regierungsmehrheit in %)

Das ergäbe bei 299 Wahlkreisen und einer Regierungsmehrheit von 55 % int(200 ∗ 299 / 55) = 1087 Parlamentssitze. 

Wenn auf die Forderung nach Repräsentation durch die Regierungsmehrheit verzichtet wird, bestimmt sich die Parlamentsgröße einfach durch 2 * Anzahl Wahlkreise. Das ergäbe bei 299 Wahlkreisen 598 Parlamentssitze.

Auch bei dem alten Wahlverfahren mit Überhangs- und Ausgleichsmandaten hatte nicht jeder Wahlkreis einen Repräsentanten in der Regierungsfraktion, und es hat niemanden gestört.
Wie viel der Gesellschaft eine vollständige Repräsentation aller Wahlkreise in der Regierungsfraktion wert ist, ist eine gesamtgesellschaftliche Diskussion, die hier nicht vorweggenommen werden kann. In der Simulation ist die Wahlkreisrepräsentation deshalb konfigurierbar, damit beide Fälle durchgespielt werden können.

Parametername: **ElectionConfig.constituency_representation** <br>
Mögliche Werte: 
 - **ENTIRE_PARLIAMENT** (Ganzes Parlament)
 - **GOVERNING_MAJORITY** (Regierungsmehrheit)

Wenn eine ja/nein Frage, wie z.B. "Welche von zwei Parteien soll regieren?" mit nur kleinen prozentualen Unterschieden vom Wähler entschieden wird, ist das Ergebnis eher als Zufall und nicht als Wählerwille zu werten. Es gibt immer Menschen, die ihre Entscheidung erst in der Wahlkabine treffen, und wäre die Wahl auch nur ein Tag später oder früher gewesen, hätten sie vielleicht anders entschieden. Der Brexit mit 51,9 % für "Austritt" und 48,1 % für "Bleiben", war eigentlich so eine Entscheidung, wo beide Gruppen im Grunde genommen gleich groß waren. Sie hätten auch losen können.

Um solche stochastischen Effekte zu vermeiden, ist es sinnvoll einen "Mindestgewinnerabstand" einzuführen, um einen Wahlgang zu gewinnen. Dieser Abstand kann in Stimmenprozent oder in Mandaten angegeben, oder auch als qualifizierte Mehrheit ausgedrückt werden. 
In der Simulation gibt es die Klasse **SuperMajorityMargin** um einen Abstand wahlweise in Sitzen oder in Prozent auszudücken.

Ein Gewinnerabstand ist an zwei Stellen im Verfahren sinnvoll:
 - Als ggf. zugesprochen Regierungsmehrheit im Parlament. Damit die Regierung die Mehrheit auch behält, wenn mal jemand krank ist, soll sie z. B. 10 Sitze mehr als die Hälfte der Parlamentssitze haben. Oder sie soll soviel mehr Sitze haben, dass sie rund 5 % mehr Stimmen als der Rest des Parlaments hat. Der Parameter, um den "Regierungsabstand" und damit indirekt die Regierungsmehrheit zu setzen, ist **ElectionConfig.parliament_majority_margin**.
 - Als Gewinnermehrheit eines Wahldurchgangs. Um einen Wahlgang zu gewinnen, reichen nicht unbedingt 50 %, sondern **ElectionConfig.ballot_majority_margin**. 

## Globale Konfiguration in der Simulation
In der Simulation hält die Klasse {class}`~ipres.election_config.ElectionConfig` alle Parameter, die für die gesamte Wahl gültig sind. Das wären im Einzelnen:  

| Parameter                   | Kurzbeschreibung                                                                                                                                                   |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| constituencies_config       | Tabelle der Wahlkreise                                                                                                                                             |
| participating_parties       | Teilnehmende Parteien                                                                                                                                              |
| parliament_majority_margin  | "Parlamentsabstand" in Sitzen oder Prozent. Wieviele Parlamentssitze oder Stimmprozent die Regierung mehr als die Opposition im Parlament haben soll. Siehe Erklärung oben. |
| ballot_majority_margin      | Mindestabstand über 50 %, den ein Kandidat in einem Wahlgang erreichen muss. Standard: 2 % (d. h. 52 %). Siehe Erklärung oben.                                        |
| draw_lots_strategy          | Standardmethode, wie man Gleichstände auflöst. Kann bein einzelnen Wahlgängen überschrieben werden. Standardwert: RANDOM (zufällig)                                |
| seed                        | Startwert für den Zufallsgenerator. Standard: None (Startwert wird zufällig gewählt.)                                                                              | 
| constituency_representation | Wahlkreisrepräsentation. Mögliche Werte: ENTIRE_PARLIAMENT, GOVERNING_MAJORITY. Siehe Erklärung im vorigen Kapitel.  Standard: ENTIRE_PARLIAMENT                  |
| language                    | Ausgabesprache für Tabellen und Diagramme. Mögliche Werte: `Language.DE` (Deutsch, Standard), `Language.EN` (Englisch). Betrifft Spaltenüberschriften, Beschriftungen, Diagrammtitel und Zahlenformatierung. |
| seat_distribution_method    | Standardmethode der proportionalen Sitzverteilung für `SeatDistributor` und `ElectionEvaluator`. Mögliche Werte: `SAINTE_LAGUE`, `D_HONDT`, `HARE_NIEMEYER`. Standard: `SAINTE_LAGUE`. Kann bei den Evaluatorklassen überschrieben werden. |
| quota_correction_strategy   | Standardstrategie zur Quotenkorrektur bei Parteien mit ungerader Sitzzahl für `ConstituencyCountDeterminer` und `ElectionEvaluator`. Mögliche Werte: `FAVOR_LARGE_PARTIES`, `FAVOR_SMALL_PARTIES`, `PROPORTIONAL`, `PROPORTIONAL_REVERSED`, `RANDOM`, `NEGOTIATED`. Standard: `FAVOR_LARGE_PARTIES`. Kann bei den Evaluatorklassen überschrieben werden. |
| constituency_allocation_method | Standardalgorithmus für die Wahlkreiszuweisung für `ConstituencyAssigner` und `ElectionEvaluator`. Mögliche Werte: `OPTIMAL`, `GREEDY`, `STABLE_MATCHING`. Standard: `OPTIMAL`. Kann bei den Evaluatorklassen überschrieben werden. |
Das Notebook
[notebooks/de/globale_konfiguration.ipynb](notebooks/de/globale_konfiguration.ipynb) demonstriert die Konfigurationsmöglichkeiten der {class}`~ipres.election_config.ElectionConfig` Klasse.

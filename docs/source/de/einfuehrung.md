# Das Wahlverfahren

## Einleitung und Motivation

In Deutschland kommt eine Form von Verhältniswahlrecht zum Einsatz. Das Ziel des Verhältniswahlrechts ist, die wichtigsten gesellschaftlichen Kräfte annähernd proportional im Parlament zu repräsentieren. Das soll die Akzeptanz des Parlaments in der Bevölkerung erhöhen und für gesellschaftliche Stabilität sorgen. Der Nachteil dieses Systems liegt auf der Hand: Wenn es viele Parteien gibt, dann ist es relativ unwahrscheinlich, dass eine Partei allein die absolute Mehrheit erlangen kann. Daraus folgt der Zwang zu oft ungewollten Koalitionen, bei denen die Parter sich gegenseitig blockieren und keiner seiner Wahlversprechen wirklich halten kann. Oder es werden mehrfach Wählergeschenke verteilt. Jeder Koaltionsparter versucht seine Klientel zufriedenzustellen, und am Ende wird der Haushalt unfinanzierbar.

Das vorgestellte Wahlverfahren schlägt als Kompromiss vor, die Reflexion der gesellschaftlichen Kräfteverhältnisse auf die Opposition zu beschränken. Durch ein iteratives Verfahren wird so lange gewählt, bis eine Gewinnerpartei feststeht. Nach wie vor sind auch Koalitionen möglich. Im Gegensatz zu früher sind sie aber kein Zwang mehr, wenn keine Partei im ersten Anlauf die absolute Mehrheit erreicht. Das Wahlverfahren sorgt dafür, dass es am Ende eine Gewinnerpartei gibt, die von mindestens der Hälfte der Wähler gewählt worden ist, wenn es auch für viele nur eine Wahl "des kleineren Übels" war. Dieser Gewinnerpartei (oder Koalition) wird eine Mehrheit der Size zugesprochen. Die restlichen Sitze werden dann unter den Oppositionsparteien proportional nach dem Ergebnis des ersten Wahlgangs verteilt.

Eine deutsche Spezialität ist die "personalisierte Verhältniswahl". Mit der "Zweitstimme" wird das Verhältnis der Parteien bestimmt und mit der "Erststimme" können unter Vorbehalt einer ausreichenden Zweitstimmendeckung bestimmte Kandidaten ins Parlament gewählt werden. Bei dem aktuell zur deutschen Bundestagswahl verwendeten System kann es vorkommen, dass einzelne Wahlkreise keine Representation im Parlament haben, da die Partei des Gewinnerkandidaten eines Wahlkreises nach dem Zweitstimmenergebnis keinen Sitz für den Direktkandidaten mehr übrig hat. Nach dem vorher verwendeten System konnte dies nicht passieren. Dafür blähte sich der Bundestag bei zunehmenden Diskrepanzen zwischen Erst- und Zweitstimmenergebnissen immer weiter auf. Deswegen wurde das alte System durch das aktuelle ersetzt.

Das vorgeschlagene Verfahren weicht von dem Prinzip des Wahlkreisgewinners ab, um Direktkandidaten in das Parlament zu wählen. Stattdessen sollen die Parteien verpflichtet werden, pro Wahlkreis mit drei Kandidaten anzutreten. Die Wähler dürfen in ihrem Wahlkreis bei jeder antretenden Partei eine "Abgeordnetenstimme" (Erststimme) für ihren Wunschkandidaten abgeben, auch wenn es nicht ihre Partei ist. Pro Partei haben die Wähler in ihrem Wahlkreis je eine Abgeordnetenstimme. Nach einem Verfahren, welches die **relative Wichtigkeit** eines Wahlkreises für eine Partei anhand der "Parteienstimmenverteilung" (Zweitstimmenverteilung) über die Wahlkreise bestimmt, werden den Wahlkreisen Parteien zur Representation zugeteilt. Der Kandidat mit den meisten Abgeordnetenstimmen der repräsentierenden Partei kommt ins Parlament.
Dieses Verfahren garantiert, dass jeder Wahlkreis eine Vertretung im Parlament hat und dass das Parteienstimmenergebnis (Zweitstimmenergebnis) bei gleichbleibender Parlamentsgröße trotzdem nicht verändert wird. Es kann nicht garantieren, dass die vertretende Person in jedem Fall der Kandidat mit den meisten Abgeordnetenstimmen pro Wahlkreis ist. Es ist nur der Kandidat mit den meisten Abgeordnetenstimmen bei der diesen Wahlkreis repräsentierenden Partei in diesem Wahlkreis.

**Hinweis**: Die Auswahl der Abgeordneten aus den drei Direktkandidaten pro Partei anhand ihres Abgeordnetenstimmenergebnisses ist nicht Teil der Simulation, da dies trivial ist und die Simulation nur unnötig aufblähen würde. Alle Stimmen in dieser Simulation sind Parteienstimmen. Nicht trivial ist aber die Zuweisung der Parteien zu Wahlkreisen anhand der Parteienstimmenverteilung. Dies ist Teil der Simulation.

---

## Überblick über die Verfahrensschritte

Das Verfahren besteht aus mehreren Schritten. Die Simulation ist so gestaltet, dass eine ganze Wahl am Anfang konfiguriert und in einem Lauf bis zu Ende durchgeführt werden kann, oder jeder Schritt einzeln durchgeführt werden kann. Dabei ist allerdings zu beachten, dass manche Schritte nicht nur von vorherigen Wahlgängen, sondern auch von Eingangskonfigurationen abhängen.

### 1. Globale Konfiguration
Zuerst muss festgelegt werden:
- Welche Wahlkreise es gibt
- Welche Parteien an der Wahl teilnehmen
- Wie groß die Regierungsmehrheit sein soll
- Ob die Wahlkreise vom gesamten Parlament oder nur von der Regierungsmehrheit representiert werden sollen. **Hinweis**: Dieser Punkt bestimmt die Größe des Parlaments. Details siehe [Globale Konfiguration](globale_konfiguration.md)

### 2. Iterative Verhältniswahl mit garantiertem Gewinner
Es wird eine iterative Verhältniswahl durchgeführt, bei der garantiert eine Partei oder Koalition gewinnt. Details siehe [Iterative Verhältniswahl](iterative_verhältniswahl.md)

### 3. Auswertung
Nachdem die Durchführung der Wahl abgeschlossen ist, findet die Auswertung statt. Sie zerfällt in die folgenden drei Phasen:
- [Mandatszuteilung](mandats_zuteilung.md)
- [Wahlkreisanzahlbestimmung pro Partei](wahlkreis_anzahl_zuordnung.md)
- [Wahlkreiszuordnung nach relativer Wichtigkeit](partei_wahlkreis_zuordnung.md)

`ElectionEvaluator.evaluate()` führt alle drei Schritte automatisch in der richtigen Reihenfolge aus. Die zugehörigen Klassen `SeatDistributor`, `ConstituencyCountDeterminer` und `ConstituencyAssigner` können bei Bedarf auch einzeln aufgerufen werden.

Eine interaktive Demonstration aller drei Schritte mit ihren Konfigurationsoptionen findet sich im Notebook [Wahlauswertung](../../notebooks/de/wahlauswertung.ipynb).

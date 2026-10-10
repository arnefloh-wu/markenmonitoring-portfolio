# Markenmonitoring — Portfolio

**Alle Daten in diesem Repository sind synthetisch.** Marken, Befragte und
Zahlen sind erfunden. Gezeigt werden Methode und Darstellung einer
zweiländrigen Markenstudie mit Vergleichswelle — nicht die Lage eines realen
Marktes.

**→ [Interaktiven Markenmonitor öffnen](https://arnefloh-wu.github.io/markenmonitoring-portfolio/)**
**→ [Gesamtdeck ansehen (49 Folien, PDF)](decks/FALLSTUDIE_GESAMT.pdf)**

---

## Die Fallstudie

ZINTO ist ein fiktiver Herausforderer in einer FMCG-Kategorie — eine Marke,
die sich über Clean Label differenziert: stark im Heimatmarkt, im
Nachbarmarkt praktisch unbekannt. Die Auswertung führt zwei Länder und zwei
Erhebungswellen zusammen und muss dabei vier Probleme lösen, die in realen
Trackings regelmäßig auftreten.

### 1. Zwei Märkte, die man nicht zusammenzählen darf

Verschiedene Grundgesamtheiten, verschiedene Quotenpläne, eine um den Faktor
sieben verschiedene Bekanntheit. Jede Kennzahl gilt für ihr Land; der Monitor
stellt sie nebeneinander, nie gepoolt. Das Markenraster unterscheidet sich
zwischen den Ländern — eine Marke, die in einem Land nicht abgefragt wurde,
erscheint dort nicht, statt als Null.

### 2. Eine Vergleichswelle mit anderem Antwortformat

Die Altwelle stammt von einem anderen Institut: Matrix mit Zwangsentscheidung
statt Ankreuzliste. Das hebt **alle** Marken an — die Niveaus beider Wellen
sind deshalb nicht voneinander abziehbar. Die Auswertung trennt beides:

- **Rangmaße** innerhalb einer Welle brauchen keine Annahme. Von 18 Marken
  legt genau eine zu; der Formatwechsel traf alle gleichzeitig und kann das
  nicht erklären.
- **Bereinigung** über die Kontrollmarken: Deren Verschiebung wird auf der
  Logitskala gegen ihr Ausgangsniveau regressiert und an der Hauptmarke
  ausgelesen. Intervall aus einem Fall-Bootstrap. Die Annahme dahinter wird
  benannt, nicht versteckt.

### 3. Eine Altstichprobe mit eingebauter Falle

Die Rohdatei der Altwelle enthält zwei Stichproben: eine Hauptstichprobe und
eine reine Jugendaufstockung. Gepoolt wären über die Hälfte der Fälle unter
30 — bei einer Marke, deren Bekanntheit mit dem Alter stark fällt, verschiebt
das die Quote um mehrere Punkte. Nur die Hauptstichprobe wird gewichtet.

### 4. Fallzahlen, die nicht alles tragen

Im Zweitmarkt kennen rund 60 Befragte die Marke. Markenbild, Treiberzerlegung
und Segmentanalyse werden dort deshalb **nicht gerechnet**, statt Zahlen mit
Nachkommastellen ohne Aussagekraft zu zeigen. Der Monitor unterdrückt
Kanalschnitte unter zwölf Fällen und sagt, warum.

## Methodisches im Einzelnen

| | |
|---|---|
| Gewichtung | Nachschichtung auf Alter × Geschlecht, Designeffekt und effektives n ausgewiesen |
| Intervalle | Wilson auf der effektiven Fallzahl, Newcombe für Differenzen |
| Multiples Testen | Holm-Korrektur über das Markenset |
| Modelle | Logistische Regression mit Likelihood-Ratio-Test je Merkmal und adjustierten Vorhersagen statt Indikatorkoeffizienten |
| Trend | Cochran-Armitage über geordnete Stufen |
| Robustheit | Fall-Bootstrap, E-Values, Sensitivitätsrechnungen an den Definitionsgrenzen |
| Textauswertung | regelbasiert und nachvollziehbar, mit ausgewiesener Trefferquote |

Separation, zu dünne Zellen und defekte Variablen werden erkannt und
ausgewiesen, nicht überrechnet. Wo ein Modell an den Rand läuft, steht das
rohe Intervall daneben.

## Die Decks

| Deck | Umfang |
|---|---|
| [Gesamtdeck](decks/FALLSTUDIE_GESAMT.pdf) | 49 Folien, alle fünf Kapitel plus Anhang |
| [Heimatmarkt](decks/FALLSTUDIE_AT.pdf) | Position, Funnel, Markenbild, Kanäle, vier Hebel |
| [Zweitmarkt](decks/FALLSTUDIE_DE.pdf) | fehlende Bekanntheit, nicht fehlende Anziehungskraft |
| [Gegenüberstellung](decks/FALLSTUDIE_VERGLEICH.pdf) | beide Märkte nebeneinander |
| [Demografie](decks/FALLSTUDIE_DEMOGRAFIE.pdf) | wer die Marke kennt, adjustierte Vorhersagen |
| [Wellenvergleich](decks/FALLSTUDIE_WELLEN.pdf) | Formateffekt getrennt vom echten Zuwachs |

## Dass die Daten synthetisch sind, können Sie nachprüfen

Der Generator liegt bei: [`builder/`](builder/). Er erzeugt die Rohdateien im
Format der jeweiligen Erhebung; die Auswertungspipeline läuft unverändert
darauf. Das Modell dahinter steht vollständig im Skript — Altersgefälle,
Geschlechtsgefälle, Clean-Label-Motivation, Formateffekt der Altwelle und
Feldqualitätsunterschiede zwischen den Ländern sind dort als Parameter
sichtbar.

## Kontakt

Dr. Arne Floh — Markenforschung, Brand Tracking, quantitative Marktforschung.
Wenn Sie eine Studie dieser Art planen oder eine bestehende prüfen lassen
wollen, schreiben Sie mir gern.

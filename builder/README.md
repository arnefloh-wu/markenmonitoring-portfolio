# Wie die Fallstudie entsteht

Die Fallstudie ist **kein Nachbau**. Es ist dieselbe Auswertungspipeline, die
auf einer echten Studie entwickelt wurde — Aufbereitung, Gewichtung,
Analysen, Decks, Dashboard —, nur auf erfundenen Eingangsdaten. Deshalb
tragen die Ergebnisse dieselben Eigenheiten wie echte: Rasterrauschen,
Separation in dünnen Zellen, Marken, die in einem Land nicht abgefragt
wurden.

Der Ablauf, hergestellt von `bauen.py`:

1. Pipeline ins Zielverzeichnis kopieren
2. Markennamen, Dateinamen und reale Unternehmensnamen ersetzen
3. Kategoriebegriffe neutralisieren und die Palette setzen
4. Fragebogendateien mit fiktiven Etiketten erzeugen (`qsf_demo.py`)
5. Synthetische Rohdaten erzeugen (`synthetik.py`)
6. Aufbereitung, Analysen, Decks und Dashboard laufen lassen

## Die Dateien

| Datei | Aufgabe |
|---|---|
| `synthetik.py` | das generative Modell. Erzeugt drei Rohdateien im Format der jeweiligen Erhebung. Alle Parameter stehen oben im Skript. |
| `marken_demo.py` | die fiktiven Marken und ihre Codes |
| `qsf_demo.py` | baut die Fragebogendateien mit fiktiven Etiketten |
| `bauen.py` | führt alles zusammen: Kopieren, Umschreiben, Palette, Prüfungen, Lauf |

## Was hier fehlt, und warum

`bauen.py` und `qsf_demo.py` importieren ein Modul `vorlage.py`. Es enthält
alles, was die Studie beim Namen nennt, an der die Pipeline entwickelt wurde:
Dateipfade, den dortigen Markennamen, die Marken des Wettbewerbs, die
genannten Unternehmen und die Formulierungen der Warengruppe — also genau
die Angaben, die der Builder ersetzt.

Dieses Modul bleibt im privaten Studienrepository. Es hier mitzuliefern
hieße, die Anonymisierung durch die Hintertür wieder aufzuheben: Wer die
Ersetzungstabelle hat, liest die Vorlage daraus ab.

Der Mechanismus ist davon unberührt — er steht vollständig in den Dateien
hier. Was fehlt, sind die Eingaben, und die wären ohne die Rohdaten der
Vorlagenstudie ohnehin nutzlos. **Der Builder ist deshalb lesbar, aber nicht
lauffähig.**

`synthetik.py` und `marken_demo.py` sind vollständig: Der Generator bekommt
die wenigen Angaben zur Vorlage (wo deren Exportdateien liegen, wie die
dortige Marke und die Segmentspalte heißen) über Umgebungsvariablen und
nennt selbst keinen realen Namen. Das Modell, das die Zahlen erzeugt, lässt
sich also ganz lesen — und darauf kommt es an, wenn man prüfen will, dass
die Daten erfunden sind.

## Drei Prüfungen, die beim Bauen abbrechen

Anonymisierung von Hand ist unzuverlässig; deshalb prüft der Lauf sich
selbst und bricht ab, statt stillschweigend etwas durchzulassen:

1. **Kategoriebegriffe in den umgeschriebenen Dateien.** Formuliert die
   Vorlagenstudie etwas neu, fällt das beim Bauen auf und nicht im fertigen
   Deck.
2. **Kategoriebegriffe in den erzeugten Rohdaten.** Die Kopfzeilen der
   Rohdateien tragen die Fragetexte; auch sie müssen neutral sein.
3. **Etiketten im Fragebogen ohne fiktive Entsprechung.** Eine Marke, die
   die Ersetzungstabelle nicht kennt, behielte sonst ihren echten Namen.

Prüfung 1 und 3 haben beim Bau dieser Fassung jeweils einen echten Fall
gefunden.

# -*- coding: utf-8 -*-
"""Erzeugt den synthetischen Rohdatensatz der Fallstudie ZINTO.

Aufruf:  python3 synthetik.py

ALLE Daten sind erfunden. Erzeugt werden drei Rohdateien im Format der
jeweiligen Erhebung, damit die Auswertungspipeline unveraendert darauf laeuft:

  ZINTO_AT_Sep2026_export.csv   Export der Befragungssoftware, Oesterreich
  ZINTO_DE_Sep2026_export.csv   Export der Befragungssoftware, Deutschland
  altwelle_2022/Rohdaten_...    Altwelle im Format des Zweitinstituts

Das Modell dahinter ist bewusst einfach und steht vollstaendig hier. Es
erzeugt die Eigenschaften, an denen sich die Auswertung zeigen laesst:

  - ein Altersgefaelle und ein Geschlechtsgefaelle bei der Hauptmarke
  - einen Zusammenhang mit der Clean-Label-Motivation
  - einen Funnel mit realistischen Uebergangsraten und etwas Rasterrauschen
    (Kauf ohne Bekanntheit), damit die hierarchische Bereinigung etwas zu
    tun hat
  - einen zweiten Markt auf einem Neuntel des Niveaus
  - eine Altwelle mit ECHTEM Wachstum UND einem Formateffekt, der alle
    Marken nach oben zieht: nur so laesst sich zeigen, wie beides getrennt
    wird
  - Quotenabweichungen, Speeder und durchgefallene Aufmerksamkeitspruefungen
    in unterschiedlicher Hoehe je Land

Was es NICHT erzeugt: eine Aussage ueber irgendeinen realen Markt.
"""
import csv, io, json, math, os, random, re

from marken_demo import MARKEN, HELD, HELD_NAME, MARKEN_2022, AUSSERHALB, RAUSCHEN

ZUFALL = random.Random(20260907)


def vorlage(name):
    """Angabe zur Vorlagenstudie aus der Umgebung holen.

    Die Rohdateien uebernehmen Kopfzeilen und Spaltenraster aus den Exporten
    der Studie, an der die Pipeline entwickelt wurde. Welche Dateien das sind
    und wie die dortige Marke heisst, setzt bauen.py - so steht in diesem
    Skript kein realer Name und es laesst sich vollstaendig zeigen.
    """
    wert = os.environ.get(name)
    if not wert:
        raise SystemExit(
            '%s ist nicht gesetzt. synthetik.py uebernimmt die Kopfzeilen der '
            'Vorlagenexporte und wird deshalb ueber bauen.py aufgerufen.' % name)
    return wert

# --- Grundbekanntheit je Marke und Land, Welle 2026 -----------------------
# Die Hauptmarke steht hier als Basiswert; Alter, Geschlecht und
# Clean-Label-Motivation verschieben ihn je Befragten.
BASIS = {
    #        AT     DE
    '1':  (0.85,  0.69),   # Avelio
    '2':  (0.09,  0.08),   # Nutrika
    '3':  (0.91,  0.81),   # Carelux
    '4':  (0.71,  0.73),   # Granova
    '5':  (0.80,  None),   # Alpenklar, nur AT
    '6':  (0.74,  0.85),   # Veranto
    '7':  (0.02,  None),   # Purlino, nur AT
    '8':  (0.88,  0.83),   # Silvano
    '9':  (0.88,  0.84),   # Frischal
    '10': (0.89,  0.34),   # Almkraft: AT-Traditionsmarke, in DE schwach
    '11': (0.94,  0.88),   # Orbix
    '12': (0.94,  0.86),   # Lunara
    '13': (0.47,  0.070),  # ZINTO
    '14': (0.10,  0.12),   # Nordfit
    '15': (0.05,  0.06),   # Clarivo
    '16': (0.72,  0.73),   # Snapup
    '17': (0.91,  0.87),   # Levito
    '18': (0.13,  0.11),   # Protera
    '19': (0.28,  0.23),   # Nutriq
    '20': (0.12,  None),   # Sportlab, nur AT
    '90': (None,  0.10),   # Norvita, nur DE
    '91': (None,  0.03),   # Purelia, nur DE
    '92': (None,  0.86),   # Zweiklang, nur DE
}
# Marken des Clean-Label-Segments: dort wirkt die Motivation mit
CLEAN = {'2', '7', '13', '14', '15', '18', '19', '20', '90', '91'}

# Welle 2022: wahres Niveau der Hauptmarke VOR dem Formateffekt.
# Der Zuwachs bis 2026 ist echt, der gemessene Unterschied faellt wegen des
# Formateffekts kleiner aus - genau die Konstellation, die die Methode
# auseinanderhalten muss.
BASIS_2022 = {'AT': 0.25, 'DE': 0.055}
FORMAT_EFFEKT = 0.72      # Logit-Aufschlag der Matrix gegenueber der Liste

ALTER = ['2', '3', '4', '5', '6']
BUNDESLAND_AT = {'1': 0.23, '2': 0.18, '3': 0.21, '4': 0.05, '5': 0.12,
                 '6': 0.08, '7': 0.06, '8': 0.04, '9': 0.03}
# Reichweite je Kanal unter den Kennern. Der Handel traegt am meisten, die
# uebrigen liegen im einstelligen bis mittleren Bereich - mit genug Masse,
# dass auch die Aufteilung nach Alter noch besetzte Zellen ergibt.
KANAL_BASIS = [0.15, 0.11, 0.11, 0.25, 0.10, 0.11, 0.09, 0.46, 0.12, 0.11]


# Zielwerte der Fallstudie. KALIB wird vor dem Erzeugen numerisch bestimmt,
# damit die Daten diese Werte tatsaechlich treffen - die Affinitaetsterme
# verschieben den Mittelwert sonst um mehrere Punkte.
ZIEL = {
    'bek_AT_2026': 0.470, 'bek_DE_2026': 0.070,
    'bek_AT_2022': 0.250, 'bek_DE_2022': 0.055,   # wahres Niveau, vor Format
    'erw_AT': 0.260, 'erw_DE': 0.230,             # Anteil unter den Kennern
}
KALIB = {}


def kalibrieren(runden=24, n=12000):
    """Achsenabschnitte numerisch bestimmen: Intervallhalbierung je Zielwert."""
    leute = {}
    for land in ('AT', 'DE'):
        leute[land] = [person(land, '2026') for _ in range(n)]
    for land in ('AT', 'DE'):
        for welle in ('2026', '2022'):
            ziel = ZIEL['bek_%s_%s' % (land, welle)]
            lo, hi = -6.0, 6.0
            for _ in range(runden):
                mitte = (lo + hi) / 2
                KALIB['bek_%s_%s' % (land, welle)] = mitte
                ist = sum(logistisch(logit(ziel) + mitte + p['aff'])
                          for p in leute[land]) / n
                if ist < ziel:
                    lo = mitte
                else:
                    hi = mitte
            KALIB['bek_%s_%s' % (land, welle)] = (lo + hi) / 2
        for land2 in (land,):
            ziel = ZIEL['erw_' + land2]
            lo, hi = -6.0, 6.0
            for _ in range(runden):
                mitte = (lo + hi) / 2
                ist = sum(logistisch(mitte + 0.34 * p['aff'])
                          for p in leute[land2]) / n
                if ist < ziel:
                    lo = mitte
                else:
                    hi = mitte
            KALIB['erw_' + land2] = (lo + hi) / 2


def logit(p):
    return math.log(p / (1 - p))


def logistisch(x):
    return 1 / (1 + math.exp(-x))


def zieh(p):
    return ZUFALL.random() < p


# Kopfzeile 2 des Vorlagenexports beschreibt die Fragen - und nennt dabei
# die Marken und die Warengruppe der Vorlage. Beides gehoert nicht in eine
# Fallstudie, die eine Methode fuer Marken des taeglichen Bedarfs zeigt.
# Deshalb werden diese Fragetexte neu geschrieben statt ersetzt: Die
# Markennamen stehen als Suffix hinter " - " und folgen dem Exportcode der
# Spalte, der Rest steht hier. Alle anderen Spalten (Demografie, Kanaele,
# Slider, Barrieren) nennen die Kategorie nicht und bleiben wie sie sind.
FRAGETEXTE = {
    'haeufigkeit': 'Wie oft kaufen Sie Produkte dieser Kategorie?',
    'spontan': 'Welche Marken dieser Kategorie fallen Ihnen spontan ein?',
    'clean': 'Wie wichtig ist es Ihnen, dass ein Produkt ohne Zusatzstoffe '
             'auskommt?',
    'bed\u00fcrfnis': 'Inwieweit erf\u00fcllt %s Ihre Bed\u00fcrfnisse in dieser '
                  'Kategorie? (0 = Gar nicht, 10 = Vollst\u00e4ndig)' % HELD_NAME,
}
RASTER_FRAGEN = {
    'bekanntheit': 'Von welchen der folgenden Marken haben Sie schon einmal '
                   'geh\u00f6rt? Mehrfachnennungen sind m\u00f6glich.',
    'betracht': 'Welche dieser Marken w\u00fcrden Sie beim n\u00e4chsten Kauf in '
                'dieser Kategorie in Betracht ziehen? Mehrfachnennungen sind '
                'm\u00f6glich.',
    'kauf_3monate': 'Welche dieser Marken haben Sie in den letzten 3 Monaten '
                    'gekauft? Mehrfachnennungen sind m\u00f6glich.',
}


def kopfzeilen(pfad):
    """Die drei Kopfzeilen eines Befragungssoftware-Exports uebernehmen.

    Uebernommen wird die Struktur, nicht der Wortlaut: Der Bezeichner der
    Segmentvariablen wandert mit (sie misst in der Fallstudie die Wichtigkeit
    von Clean Label und heisst deshalb clean), die Fragetexte werden
    kategorieneutral gefasst und die Markennamen aus dem Exportcode der
    Spalte neu gesetzt. Die Umbenennung muss hier passieren, weil die
    Aufbereitung die Spalten aus dieser Zeile liest.
    """
    r = csv.reader(io.open(pfad, encoding='utf-8-sig'))
    rohe = [next(r) for _ in range(3)]
    def um(c):
        return re.sub(r'(?<![\w])' + vorlage('VORLAGE_SEGMENTSPALTE')
                      + r'(?![\w])', 'clean', c)

    spalten = [um(c) for c in rohe[0]]
    beschreibung = []
    for name, text in zip(spalten, rohe[1]):
        teil = name.rsplit('_', 1)
        if len(teil) == 2 and teil[0] in RASTER_FRAGEN:
            text = '%s - %s' % (RASTER_FRAGEN[teil[0]],
                                MARKEN[teil[1]][0] if teil[1] in MARKEN
                                else 'KEINE Marke')
        text = FRAGETEXTE.get(name, text)
        beschreibung.append(text.replace(vorlage('VORLAGE_MARKE'),
                                         HELD_NAME))
    return [spalten, beschreibung, [um(c) for c in rohe[2]]]


# --------------------------------------------------------------- Befragte
def person(land, welle):
    """Ein Befragter mit Demografie und latenter Markenaffinitaet."""
    # Alter: das Feld liefert die jungen Zellen schlechter als geplant
    # Nahe am Quotenplan, aber mit der typischen Schieflage: die jungen
    # Zellen laufen schlechter voll, die aelteren ueber. Zu grosse
    # Abweichungen wuerden die Gewichte aufblaehen und die Zellen leeren.
    a = ZUFALL.choices(ALTER, weights=[0.19, 0.20, 0.20, 0.21, 0.20])[0]
    g = ZUFALL.choices(['1', '2'], weights=[0.51, 0.49])[0]
    clean = ZUFALL.choices(['1', '2', '3', '4', '5'],
                            weights=[0.08, 0.12, 0.22, 0.33, 0.25])[0]
    haeufig = ZUFALL.choices([str(i) for i in range(1, 8)],
                             weights=[0.03, 0.14, 0.17, 0.26, 0.17, 0.18, 0.05])[0]
    p = {'alter': a, 'geschlecht': g, 'clean': clean, 'haeufigkeit': haeufig,
         'einkommen': ZUFALL.choices([str(i) for i in range(1, 8)],
                                     weights=[.04, .15, .21, .18, .14, .18, .10])[0],
         'bildung': ZUFALL.choices([str(i) for i in range(1, 8)],
                                   weights=[.06, .31, .26, .14, .15, .03, .05])[0]}
    if land == 'AT':
        p['bundesland'] = ZUFALL.choices(list(BUNDESLAND_AT),
                                         weights=list(BUNDESLAND_AT.values()))[0]
    else:
        # Der zweite Markt liefert eine unbrauchbare Regionalangabe - ein
        # Datenfehler, den die Auswertung erkennen und ausweisen soll.
        p['bundesland'] = ZUFALL.choice([str(i) for i in range(1, 10)])
    # Affinitaet zur Hauptmarke: jung, weiblich, clean-label-affin
    p['aff'] = (0.95 - 0.42 * ALTER.index(a)
                + (0.46 if g == '2' else 0.0)
                + 0.30 * (int(clean) - 3))
    return p


def bekannt(code, land, p, welle):
    """Gestuetzte Bekanntheit einer Marke bei diesem Befragten."""
    basis = BASIS[code][0 if land == 'AT' else 1]
    if basis is None:
        return False
    if code == HELD:
        basis = BASIS_2022[land] if welle == '2022' else basis
        x = logit(basis) + KALIB['bek_%s_%s' % (land, welle)] + p['aff']
    else:
        x = logit(basis)
        if code in CLEAN:                      # jung und clean-label-affin
            x += 0.26 * (2 - ALTER.index(p['alter'])) + 0.18 * (int(p['clean']) - 3)
        else:                                   # Klassiker: altersneutral
            x += 0.05 * (2 - ALTER.index(p['alter']))
    if welle == '2022':
        x += FORMAT_EFFEKT                      # Matrix statt Ankreuzliste
    return zieh(logistisch(x))


def spontantext(land, p, kennt_held):
    """Freie Nennungen. Wer die Marke kennt, nennt sie manchmal von selbst."""
    im_raster = [c for c in MARKEN
                 if MARKEN[c][1 if land == 'AT' else 2] == 1 and c != HELD]
    gross = [c for c in im_raster if (BASIS[c][0 if land == 'AT' else 1] or 0) > 0.6]
    ZUFALL.shuffle(gross)
    namen = [MARKEN[c][0] for c in gross[:ZUFALL.randint(1, 4)]]
    # Marken ausserhalb des Rasters - der Grund, warum das Raster zu pruefen ist
    if zieh(0.34):
        namen.insert(ZUFALL.randint(0, len(namen)), ZUFALL.choice(AUSSERHALB))
    # Die Hauptmarke: nur Kenner, und auch die selten. In DE praktisch nie.
    if kennt_held and zieh(0.16 if land == 'AT' else 0.03):
        namen.insert(ZUFALL.randint(0, min(2, len(namen))), HELD_NAME)
    if zieh(0.06):
        namen.append(ZUFALL.choice(RAUSCHEN))
    if not namen or zieh(0.02):
        return ZUFALL.choice(['keine', 'weiss nicht', ''])
    trenner = ZUFALL.choice([', ', '\n', ' ', ', '])
    return trenner.join(namen)


def beschreibung(kennt, erwaegt):
    """Offene Beschreibung der Hauptmarke, nur Kenner."""
    if not kennt:
        return ''
    if not erwaegt and zieh(0.5):
        return ZUFALL.choice([
            'kenne ich zu wenig', 'noch nie probiert', 'sagt mir wenig',
            'zu teuer', 'habe ich noch nicht gekauft', 'keine Ahnung'])
    return ZUFALL.choice([
        'wenig Zusatzstoffe, schmeckt gut', 'klare Zutatenliste',
        'innovativ und praktisch', 'etwas teuer, aber gut',
        'gesunde Alternative', 'angenehme Konsistenz',
        'ohne Zusatzstoffe, gute Idee', 'moderne Marke',
        'gute Qualität für den Preis', 'teuer, aber die Qualität stimmt'])


def h1_barrieren(erwaegt, gekauft):
    """Kaufbarrieren. Gefragt werden die Erwaeger OHNE Kauf - wer die Marke
    auf der Liste hat, sie aber nicht kauft. Das ist die Gruppe, bei der
    Preis und Verfuegbarkeit ueberhaupt eine Rolle spielen koennen."""
    if not (erwaegt and not gekauft):
        return [''] * 9
    aus = [''] * 9
    # 1 zu teuer, 2 nicht verfuegbar, 3 Geschmack, 4 kein Bedarf, ...
    for i, p in enumerate([0.46, 0.31, 0.17, 0.26, 0.11, 0.09, 0.07, 0.05, 0.12]):
        if zieh(p):
            aus[i] = '1'
    if not any(aus):
        aus[ZUFALL.randint(0, 3)] = '1'
    return aus


def kanaele(land, p):
    """Kontaktkanaele, nur Kenner. Der Handel traegt am meisten."""
    aus = []
    for i, basis in enumerate(KANAL_BASIS):
        q = basis
        if land == 'DE':
            # Im zweiten Markt laeuft die Wahrnehmung ueber Social, nicht
            # ueber das Regal - die Marke steht dort kaum im Sichtfeld.
            q = basis * (0.35 if i == 7 else 1.75)
        if i in (3, 4, 5, 6):                   # Social und Creator: jung
            q *= 1.0 + 0.30 * (2 - ALTER.index(p['alter']))
        aus.append('1' if zieh(min(q, 0.95)) else '')
    if not any(aus):
        return aus + ['1']                      # "in keinem dieser Kanaele"
    return aus + ['']


def slider(kennt, p):
    """Fuenf Markenbildskalen, nur Kenner, mit Ausfaellen."""
    if not kennt:
        return [''] * 5
    kern = 34 + 7 * p['aff'] + ZUFALL.gauss(0, 22)
    aus = []
    for versatz, ausfall in ((4, 0.08), (12, 0.05), (-32, 0.08),
                             (0, 0.12), (-24, 0.12)):
        if zieh(ausfall):
            aus.append('')
        else:
            aus.append(str(int(max(-100, min(100, kern + versatz + ZUFALL.gauss(0, 16))))))
    return aus


# ------------------------------------------------------- Welle 2026, Export
def welle_2026(land, n_brutto, kopf, start_tag, tage, attention_quote,
               speeder_quote):
    """Rohdatei eines Landes im Format der Befragungssoftware."""
    spalten = kopf[0]
    zeilen = []
    for i in range(n_brutto):
        p = person(land, '2026')
        raster = [c for c in MARKEN if MARKEN[c][1 if land == 'AT' else 2] == 1]
        kennt = {c: bekannt(c, land, p, '2026') for c in raster}
        kennt_held = kennt[HELD]

        # Erwaegung und Kauf, bedingt auf Bekanntheit - plus etwas
        # Rasterrauschen, das die hierarchische Bereinigung spaeter aufraeumt.
        erw, kauf = {}, {}
        for c in raster:
            basis = BASIS[c][0 if land == 'AT' else 1] or 0
            if kennt[c]:
                q = 0.30 if c == HELD else min(0.42, 0.14 + 0.38 * basis)
                if c == HELD:
                    q = logistisch(KALIB['erw_' + land] + 0.34 * p['aff'])
                erw[c] = zieh(q)
                kauf[c] = zieh(0.55 if erw[c] else 0.030)
            else:
                erw[c] = zieh(0.007 if land == 'AT' else 0.019)
                kauf[c] = zieh(0.004 if land == 'AT' else 0.013)
        keine = '1' if not any(kennt.values()) else ''

        dauer = int(max(28, ZUFALL.lognormvariate(
            5.28 if kennt_held else 4.90, 0.46)))
        ist_speeder = zieh(speeder_quote)
        if ist_speeder:
            dauer = ZUFALL.randint(18, 58)
        att = '100'
        if zieh(attention_quote):
            att = str(ZUFALL.choice([0, 25, 50, 75]))
        unter18 = (i == 3)                       # genau ein Fall, wie im Feld

        tag = ZUFALL.choices(tage, weights=[t[1] for t in tage])[0][0] \
            if isinstance(tage[0], tuple) else ZUFALL.choice(tage)
        uhr = '%02d:%02d:%02d' % (ZUFALL.randint(7, 22), ZUFALL.randint(0, 59),
                                  ZUFALL.randint(0, 59))
        start = '%s %s' % (tag, uhr)

        z = {k: '' for k in spalten}
        z.update({
            'StartDate': start, 'EndDate': start, 'RecordedDate': start,
            'Status': '0', 'Progress': '100', 'Finished': '1',
            'Duration (in seconds)': str(dauer),
            'ResponseId': 'R_%s' % ''.join(
                ZUFALL.choice('abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ0123456789')
                for _ in range(15)),
            'DistributionChannel': 'anonymous', 'UserLanguage': 'DE',
            'Q_RecaptchaScore': '0.3' if zieh(0.06) else '1',
            'Q_PrivateBrowserDetected': 'true' if zieh(0.14) else '',
            'Last Seen Flow Element ID': 'FL_EOS_ID',
            'haeufigkeit': p['haeufigkeit'], 'alter': '1' if unter18 else p['alter'],
            'geschlecht': p['geschlecht'], 'bundesland': p['bundesland'],
            'einkommen': p['einkommen'], 'bildung': p['bildung'],
            'attention_1': att, 'clean': p['clean'],
            'spontan': spontantext(land, p, kennt_held),
            'land': land, 'PID': 'P%06d' % ZUFALL.randint(1, 999999),
        })
        if att != '100':
            # Die Pruefung terminiert im Feld: danach keine Angaben mehr.
            z['Progress'] = '29'
            z['Finished'] = '0'
            zeilen.append([z.get(k, '') for k in spalten])
            continue
        for c in raster:
            z['bekanntheit_%s' % c] = '1' if kennt[c] else ''
            z['betracht_%s' % c] = '1' if erw[c] else ''
            z['kauf_3monate_%s' % c] = '1' if kauf[c] else ''
        z['bekanntheit_99'] = keine
        for i2, v in enumerate(kanaele(land, p) if kennt_held else [''] * 11):
            z['kanal_%d' % (i2 + 1)] = v
        for nm, v in zip(['emotion_1', 'qualität_1', 'plv_1', 'zufriedenheit_1',
                          'wom_1'], slider(kennt_held, p)):
            z[nm] = v
        for i2, v in enumerate(h1_barrieren(erw.get(HELD, False),
                                            kauf.get(HELD, False))):
            z['H1_%d' % (i2 + 1)] = v
        z['beschreibung'] = beschreibung(kennt_held, erw.get(HELD, False))
        if kennt_held:
            z['bedürfnis'] = str(ZUFALL.randint(2, 5))
            z['bedeutsam'] = str(ZUFALL.randint(2, 5))
            z['intention'] = str(ZUFALL.randint(1, 5))
            z['empfehlung'] = str(ZUFALL.randint(0, 10))
        for sp in spalten:
            if sp.endswith(('First Click', 'Last Click', 'Page Submit')):
                z[sp] = '%.3f' % (ZUFALL.random() * 40 + 1)
            elif sp.endswith('Click Count'):
                z[sp] = str(ZUFALL.randint(1, 9))
        zeilen.append([z.get(k, '') for k in spalten])
    return zeilen


# ------------------------------------------------------- Welle 2022, Altformat
def welle_2022(kopf22):
    """Rohdatei im Format des Zweitanbieters: beide Laender in einer Datei,
    dazu eine Jugendaufstockung, die als Falle in den Daten liegt."""
    spalten = kopf22
    q20 = {}                        # Q20A<n> -> Markencode
    for n, code in enumerate(MARKEN_2022, 1):
        q20['Q20A%d' % n] = code
    # Altersbaender des Zweitanbieters: 11 Stufen, feiner als 2026
    ALT22 = {'2': ['2'], '3': ['3', '4'], '4': ['5', '6'],
             '5': ['7', '8'], '6': ['9', '10']}
    zeilen = []
    lfd = 0
    for sample, n_je_land in (('1', 1000), ('2', 600)):
        for land_code, land in (('1', 'AT'), ('2', 'DE')):
            for _ in range(n_je_land):
                lfd += 1
                p = person(land, '2022')
                if sample == '2':
                    # Jugendaufstockung: ausschliesslich 14 bis 29
                    p['alter'] = '2'
                    p['aff'] = 0.95 + 0.30 * (int(p['clean']) - 3) \
                        + (0.46 if p['geschlecht'] == '2' else 0.0)
                q3 = ZUFALL.choice(ALT22[p['alter']])
                if sample == '2':
                    q3 = ZUFALL.choice(['2', '3', '4'])
                z = {k: '' for k in spalten}
                z['ID'] = str(100000 + lfd)
                z['Q1'] = land_code
                z['Q2'] = '3' if zieh(0.0025) else p['geschlecht']
                z['Q3'] = q3
                if land == 'AT':
                    z['Q4'] = p['bundesland']
                z['Q5'] = ZUFALL.choice(['1', '2', '3', '4'])
                # Q12A3: Zustimmung zu "achte auf Zusatzstoffe", umgekehrte Skala
                z['Q12A3'] = str(6 - int(p['clean']))
                z['Q13A4'] = p['haeufigkeit']
                z['Q17'] = str(ZUFALL.randint(1, 8))
                for q, code in q20.items():
                    basis = BASIS[code][0 if land == 'AT' else 1]
                    if basis is None:
                        z[q] = '2'
                        continue
                    z[q] = '1' if bekannt(code, land, p, '2022') else '2'
                z['Q18A1'] = spontantext(land, p, z['Q20A%d' % (
                    MARKEN_2022.index(HELD) + 1)] == '1') if zieh(0.92) else ' '
                z['Sample'] = sample
                zeilen.append([z.get(k, '') for k in spalten])
    ZUFALL.shuffle(zeilen)
    return zeilen


def main():
    kalibrieren()
    print('Kalibrierung: ' + '  '.join(
        '%s %+.2f' % (k, v) for k, v in sorted(KALIB.items())))
    kopf_at = kopfzeilen(vorlage('VORLAGE_EXPORT_2026'))
    # Oesterreich: sauberes Feld. Deutschland: schlechtere Feldqualitaet,
    # mehr Durchfaller, kuerzere Bearbeitungszeit - der Befund, den der
    # Feldbericht spaeter ausweist.
    laender = [
        ('AT', 'ZINTO_AT_Sep2026_export.csv', 648,
         ['2026-09-25'] * 5 + ['2026-09-26', '2026-09-27'] + ['2026-09-28'] * 6
         + ['2026-09-29', '2026-09-30'], 0.029, 0.043),
        ('DE', 'ZINTO_DE_Sep2026_export.csv', 1240,
         ['2026-09-25', '2026-09-26', '2026-09-27'] + ['2026-09-28'] * 6
         + ['2026-09-29'] * 8 + ['2026-09-30'] * 7 + ['2026-10-01',
                                                      '2026-10-02', '2026-10-03'],
         0.121, 0.092),
    ]
    for land, aus, n, tage, att, spd in laender:
        zeilen = welle_2026(land, n, kopf_at, None, tage, att, spd)
        with io.open(aus, 'w', encoding='utf-8-sig', newline='') as fh:
            s = csv.writer(fh)
            s.writerows(kopf_at)
            s.writerows(zeilen)
        print('Geschrieben: %-32s %4d Datensaetze' % (aus, len(zeilen)))

    kopf22 = next(csv.reader(io.open(vorlage('VORLAGE_EXPORT_2022'),
                                     encoding='utf-8-sig'),
                             delimiter=';'))
    zeilen = welle_2022(kopf22)
    os.makedirs(os.environ['ALTWELLE'], exist_ok=True)
    aus22 = (os.environ['ALTWELLE'] + '/'
             'Rohdaten_ZINTO_Bekanntheit und Image AT+DE_September 2022.csv')
    with io.open(aus22, 'w', encoding='utf-8-sig', newline='') as fh:
        s = csv.writer(fh, delimiter=';')
        s.writerow(kopf22)
        s.writerows(zeilen)
    print('Geschrieben: %-32s %4d Datensaetze' % ('Altwelle 2022', len(zeilen)))


if __name__ == '__main__':
    main()

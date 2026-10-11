# -*- coding: utf-8 -*-
"""Baut die Fallstudie ZINTO aus der echten Auswertungspipeline.

Aufruf:  python3 fallstudie/bauen.py [zielverzeichnis]

Die Fallstudie ist kein Nachbau, sondern dieselbe Pipeline auf anderen
Eingangsdaten. Dieses Skript stellt das her, damit es nicht von Hand
wiederholt werden muss:

  1  Pipeline ins Zielverzeichnis kopieren
  2  Markennamen, Dateinamen und reale Unternehmensnamen ersetzen
  3  Kategoriebegriffe neutralisieren und die Blaupalette setzen
  4  Fragebogendateien mit fiktiven Etiketten erzeugen (qsf_demo.py)
  5  Synthetische Rohdaten erzeugen (synthetik.py)
  6  Aufbereitung, Analysen, Decks und Dashboard laufen lassen

Was dabei ersetzt wird und warum, steht in vorlage.py - dem einzigen Modul,
das die Vorlagenstudie beim Namen nennt und deshalb nicht mitveroeffentlicht
wird. Zwei Regeln dahinter: In einer Fallstudie mit erfundenen Zahlen darf
kein realer Name stehen - weder eine Marke noch ein Institut noch eine
Handelskette. Und die Fallstudie zeigt eine Methode fuer Marken des
taeglichen Bedarfs, keine einzelne Warengruppe; deshalb traegt sie einen
neutralen Kategorierahmen und eine eigene Palette.
"""
import glob, io, os, re, shutil, subprocess, sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

from marken_demo import HELD_NAME
# Alles, was die Vorlagenstudie beim Namen nennt, steht in vorlage.py und
# nur dort - siehe das Modul. Dieses Skript zeigt den Mechanismus, nicht
# die Vorlage.
from vorlage import (QUELLE, QSF, DATEIEN, ERSETZUNGEN, KATEGORIE,
                     BEZEICHNER, VERBOTEN, NUR_IM_TEXT, EXPORT_2026,
                     EXPORT_2022, SEGMENTSPALTE)
from vorlage import MARKE as VORLAGE_MARKE

ZIEL = sys.argv[1] if len(sys.argv) > 1 else '/home/user/demo'
ALTWELLE = 'altwelle_2022'      # Ordner der Vergleichswelle, neutral benannt

PIPELINE = ['slides_basis.py', 'slides_at.py', 'slides_de.py',
            'slides_vergleich.py', 'slides_demografie.py', 'slides_wellen.py',
            'slides_gesamt.py', 'dashboard.py', 'datensatz.py',
            'aufbereitung_at.py', 'aufbereitung_de.py', 'aufbereitung_2022.py',
            'gewichtung_ziele_AT.csv', 'gewichtung_ziele_DE.csv']
MITBRINGEN = ['synthetik.py', 'marken_demo.py', 'qsf_demo.py',
              'vorlage.py']

# Farbtoken des Dashboards. Die Fallstudie laeuft in einer Blaupalette, die
# Studie in den Markenfarben; beide Modi sind mit dem Validator geprueft
# (kategorialer Abstand, Chroma, CVD, Kontrast) und die Rampe st1..st4 ist in
# beiden Modi monoton. Der dunkle Modus hat eigene Stufen, keine Umkehrung.
HELL = {'flaeche': '#fbfcfe', 'plane': '#eef2f9', 'ink': '#10172a',
        'ink2': '#5b6475', 'muted': '#8b93a3', 'grid': '#e2e6ee',
        'base': '#a3abba', 'akzent': '#1d4ed8', 'zweit': '#0d9488',
        'warnung': '#9a6700', 'st1': '#16307e', 'st2': '#1d4ed8',
        'st3': '#8fb2f6', 'st4': '#e8edf6', 'chip': '#ffffff',
        'chipan': '#1a46c2', 'chipant': '#ffffff'}
DUNKEL = {'flaeche': '#141a24', 'plane': '#0b0f16', 'ink': '#ffffff',
          'ink2': '#c2c8d4', 'muted': '#8a92a1', 'grid': '#283040',
          'base': '#636c7d', 'akzent': '#4f87ef', 'zweit': '#10a89a',
          'warnung': '#e0a33c', 'st1': '#9dbcf8', 'st2': '#3b74e8',
          'st3': '#1e3f86', 'st4': '#232c3a', 'chip': '#1d2430',
          'chipan': '#2f62d8', 'chipant': '#ffffff'}
# Dieselbe Palette fuer die Decks. marke_laden() leitet die Funnel-Rampe aus
# Akzent und Dunkelton ab, deshalb stehen hier nur die fuenf Eckwerte.
# Die Schriften kommen aus demselben Stack wie im Monitor, damit Deck und
# Seite der Fallstudie zusammenpassen; die Palette bleibt ihre eigene.
MARKE = {'akzent': HELL['akzent'], 'dunkel': HELL['st1'],
         'zweit': HELL['zweit'], 'flaeche': HELL['flaeche'],
         'ink': HELL['ink'], 'teiler': HELL['st1'],
         'rampe': [HELL['st3'], HELL['st2'], HELL['st1']],
         'schrift': 'system-ui,-apple-system,"Segoe UI",Roboto,'
                    '"Helvetica Neue",Arial,sans-serif',
         'anzeige': '"Iowan Old Style","Palatino Linotype",Palatino,'
                    '"Book Antiqua",Georgia,serif'}
# Kontakt der Fallstudie. Sie ist ein Portfoliostueck: Wer das Deck als PDF
# weitergereicht bekommt oder den Monitor geschickt bekommt, soll ohne Umweg
# sehen, von wem es stammt. Die Links werden im PDF mitgenommen.
WEB, MAIL = 'https://alpha-metrics.ai', 'info@alpha-metrics.ai'
LINKEDIN = 'https://www.linkedin.com/company/112210061/'
KONTAKT_LINKS = (
    '<a href="%s">alpha-metrics.ai</a> \u00b7 <a href="mailto:%s">%s</a> '
    '\u00b7 <a href="%s">LinkedIn</a>' % (WEB, MAIL, MAIL, LINKEDIN))
# Im Deck steht die Signatur auf der Titelfolie, im Monitor in der Fusszeile.
KONTAKT = [
    ('Dr. Arne Floh \u00b7 Oktober 2026',
     'Dr. Arne Floh \u00b7 Oktober 2026<br>' + KONTAKT_LINKS),
]
HINWEIS = 'Demonstrationsdaten \u00b7 alle Zahlen und Marken erfunden'
HINWEIS_CSS = """.s::before{content:"%s";position:absolute;top:58px;right:72px;
  font-size:10px;letter-spacing:.09em;text-transform:uppercase;font-weight:700;
  color:%%(ak)s}
.s.teiler::before{color:#fff;right:96px}
.title .meta a{color:%%(ak)s;text-decoration:none}
""" % HINWEIS
HINWEIS_H1 = ('<h1>ZINTO Markenmonitor <span class="demo">'
              'Demonstrationsdaten</span></h1>\n'
              '  <p class="kontakt">Dr. Arne Floh \u00b7 %s</p>'
              % KONTAKT_LINKS)
HINWEIS_SATZ = ('<strong>Alle Zahlen, Marken und Befragten sind '
                'erfunden.</strong>')
HINWEIS_DASH_CSS = """
.demo{display:inline-block;vertical-align:middle;margin-left:11px;
  font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--akzent);border:1px solid var(--akzent);border-radius:999px;
  padding:3px 10px}
footer a{color:var(--akzent);text-decoration:none}
footer a:hover{text-decoration:underline}
.kontakt{margin-top:8px;font-size:13.5px;color:var(--ink2)}
.kontakt a{color:var(--akzent);text-decoration:none}
.kontakt a:hover{text-decoration:underline}"""
LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 110" \
width="320" height="110">
  <rect width="320" height="110" rx="16" fill="%(akzent)s"/>
  <text x="160" y="56" text-anchor="middle" font-family="Archivo, Helvetica, Arial, sans-serif"
        font-size="46" font-weight="700" letter-spacing="2" fill="#ffffff">%(marke)s</text>
  <text x="160" y="82" text-anchor="middle" font-family="Archivo, Helvetica, Arial, sans-serif"
        font-size="13" font-weight="500" letter-spacing="4" fill="#c3d4fb">FALLSTUDIE</text>
</svg>
"""

SCHRITTE = (['aufbereitung_at', 'aufbereitung_de', 'aufbereitung_2022']
            + ['analyse_funnel_at', 'analyse_funnel_de', 'analyse_bekanntheit_at',
               'analyse_bekanntheit_de', 'analyse_bekanntheit_demografie_at',
               'analyse_brandhealth_at', 'analyse_kanaele_at', 'analyse_kanaele_de',
               'analyse_kanaele_detail_at', 'analyse_kanaele_funnel',
               'analyse_segmente_text_at', 'analyse_treiber_at',
               'analyse_weitere_at', 'analyse_wellen', 'analyse_demografie']
            + ['slides_at', 'slides_de', 'slides_vergleich', 'slides_demografie',
               'slides_wellen', 'slides_gesamt', 'dashboard'])


def markenkarte():
    """Echter Markenname -> fiktiver Name, ueber die Exportcodes verknuepft."""
    import json
    from marken_demo import MARKEN, AUSSERHALB
    echt = {}
    for land in ('AT', 'DE'):
        q = json.load(io.open(os.path.join(QUELLE, QSF % land),
                              encoding='utf-8'))
        for e in q['SurveyElements']:
            p = e.get('Payload')
            if e['Element'] == 'SQ' and isinstance(p, dict) \
                    and p.get('DataExportTag') == 'bekanntheit':
                rc = p['RecodeValues']
                for k in p['ChoiceOrder']:
                    echt.setdefault(rc[str(k)],
                                    re.sub('<[^>]+>', '', p['Choices'][str(k)]['Display']))
    karte = {echt[c]: MARKEN[c][0] for c in MARKEN if c in echt}
    # Zwei Marken stehen im Raster mit Herstellerzusatz in Klammern, im
    # Fliesstext der Auswertung aber ohne. Ohne diesen Alias bleibt der
    # reale Name dort stehen - genau das, was die Fallstudie nicht darf.
    for name, fiktiv in list(karte.items()):
        if ' (' in name:
            karte[name.split(' (')[0]] = fiktiv
    # Marken, die nur im freien Text vorkamen
    for i, n in enumerate(NUR_IM_TEXT):
        karte[n] = AUSSERHALB[i % len(AUSSERHALB)]
    return karte


def umschreiben(text, karte):
    for a, b in DATEIEN:
        text = text.replace(a, b)
    # Bezeichner und Markenname sind derselbe Text; beide wandern mit.
    text = text.replace(VORLAGE_MARKE, HELD_NAME)
    text = text.replace(VORLAGE_MARKE.lower(), HELD_NAME.lower())
    for a, b in sorted(karte.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(r'(?<![\w])' + re.escape(a) + r'(?![\w])', b, text)
    for a, b in ERSETZUNGEN:
        text = re.sub(r'(?<![\w])' + re.escape(a) + r'(?![\w])', b, text)
    for a, b in KONTAKT:
        text = text.replace(a, b)
    for a, b in KATEGORIE:
        text = text.replace(a, b)
    for a, b in BEZEICHNER:
        text = re.sub(r'(?<![\w])' + a + r'(?![\w])', b, text)
    return re.sub(r' *· *<br>', '<br>', text)


def markieren(name, text):
    """Den Hinweis auf erfundene Daten in Decks und Dashboard setzen.

    Er steht auf JEDER Folie und nicht nur auf der Titelfolie: Die Decks
    werden als PDF weitergegeben und seitenweise gelesen; ein Hinweis in
    einer Begleitdatei erreicht den Leser von Folie 23 nicht. Weiss auf dem
    Akzent erreicht 6,70:1 - genug fuer die kleine Schrift auf den
    Kapiteltrennern.
    """
    if name == 'slides_basis.py':
        anker = ('  font-size:11px;line-height:12px;color:%(muted)s;'
                 'border-top:1px solid %(grid)s;padding-top:9px}\n')
        assert anker in text, 'Fusszeilenregel in stil() nicht gefunden'
        return text.replace(anker, anker + HINWEIS_CSS, 1)
    anker = '<h1>ZINTO Markenmonitor</h1>'
    assert anker in text, 'Kopfzeile des Dashboards nicht gefunden'
    text = text.replace(anker, HINWEIS_H1, 1)
    anker = ('<span>Dr. Arne Floh \u00b7 Markenstudie ZINTO September 2026'
             '</span>')
    assert anker in text, 'Fusszeile des Dashboards nicht gefunden'
    text = text.replace(
        anker, '<span>Markenstudie ZINTO September 2026 \u00b7 '
        'Dr. Arne Floh</span>', 1)
    anker = '  <p class="sub">Markenstudie September 2026'
    assert anker in text
    text = text.replace(anker, '  <p class="sub">' + HINWEIS_SATZ
                        + ' Markenstudie September 2026', 1)
    anker = ('.sub{color:var(--ink2);font-size:14.5px;margin-top:7px;'
             'max-width:68ch}')
    assert anker in text
    return text.replace(anker, anker + HINWEIS_DASH_CSS, 1)


def farben_umstellen(text):
    """Die Farbtoken des Dashboards auf die Palette der Fallstudie setzen.

    Das Dashboard traegt seine Palette in drei :root-Bloecken: hell, dann
    zweimal dunkel (Systemvorgabe und manuelle Wahl). Gesucht wird nicht nach
    Hexwerten - derselbe Wert steht in mehreren Bloecken fuer
    unterschiedliche Rollen -, sondern blockweise nach Tokennamen. Ein Token,
    das die Tabelle kennt und das Dashboard nicht mehr fuehrt, bricht den
    Lauf; dann ist die Tabelle veraltet.
    """
    bloecke = [(':root{', HELL),
               (':root:not([data-theme="light"]){', DUNKEL),
               (':root[data-theme="dark"]{', DUNKEL)]
    gesehen = set()

    def ersetze(m, tabelle):
        gesehen.add(m.group(1))
        return '--%s:%s' % (m.group(1), tabelle.get(m.group(1), m.group(2)))

    for anker, tabelle in bloecke:
        i = text.index(anker) + len(anker)
        # Der Block endet bei der ersten Zeile, die kein Token mehr setzt -
        # und zwar HINTER der letzten Tokenzeile, sonst bleibt deren Inhalt
        # ungeaendert stehen.
        j = i
        while True:
            k = text.index('\n', j) + 1
            j = k
            if not text[k:].lstrip(' ').startswith('--'):
                break
        text = text[:i] + re.sub(r'--([a-z0-9]+):(#[0-9a-fA-F]{3,8})',
                                 lambda m: ersetze(m, tabelle),
                                 text[i:j]) + text[j:]
    fehlt = sorted(n for n in set(HELL) | set(DUNKEL) if n not in gesehen)
    if fehlt:
        raise SystemExit('Farbtabelle kennt Token, die das Dashboard nicht '
                         'mehr fuehrt: %s' % ', '.join(fehlt))
    return text


def main():
    os.makedirs(ZIEL, exist_ok=True)
    os.makedirs(os.path.join(ZIEL, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(ZIEL, ALTWELLE), exist_ok=True)
    karte = markenkarte()

    # Palette und Logo der Fallstudie. Sie gehoeren hierher und nicht von
    # Hand ins Zielverzeichnis: Sonst laeuft ein frischer Bau in den
    # Markenfarben der echten Studie.
    import json
    io.open(os.path.join(ZIEL, 'assets', 'marke.json'), 'w',
            encoding='utf-8').write(json.dumps(MARKE, indent=2) + '\n')
    io.open(os.path.join(ZIEL, 'assets', '%s-logo.svg' % HELD_NAME.lower()),
            'w', encoding='utf-8').write(
                LOGO % {'akzent': MARKE['akzent'], 'marke': HELD_NAME})

    kopiert = 0
    for name in PIPELINE + [f for f in os.listdir(QUELLE)
                            if f.startswith('analyse_') and f.endswith('.py')]:
        quelle = os.path.join(QUELLE, name)
        if not os.path.exists(quelle):
            continue
        t = io.open(quelle, encoding='utf-8').read()
        if name.endswith('.py'):
            t = umschreiben(t, karte)
            uebrig = [w for w in VERBOTEN if w in t.lower()]
            if uebrig:
                raise SystemExit(
                    '%s: Kategoriebegriffe stehen noch im Text (%s). Die '
                    'Studie formuliert etwas neu - KATEGORIE ergaenzen.'
                    % (name, ', '.join(uebrig)))
        if name in ('slides_basis.py', 'dashboard.py'):
            t = markieren(name, t)
        if name == 'dashboard.py':
            t = farben_umstellen(t)
        io.open(os.path.join(ZIEL, name), 'w', encoding='utf-8').write(t)
        kopiert += 1
    for name in MITBRINGEN:
        shutil.copy(os.path.join(HIER, name), os.path.join(ZIEL, name))
    print('Pipeline umgeschrieben: %d Dateien' % kopiert)

    # Markenmuster der Textauswertung auf die fiktiven Namen umstellen
    pfad = os.path.join(ZIEL, 'analyse_segmente_text_at.py')
    t = io.open(pfad, encoding='utf-8').read()
    from marken_demo import MARKEN, AUSSERHALB
    eintraege = [(n, re.escape(n.lower()))
                 for n in [MARKEN[c][0] for c in sorted(MARKEN, key=int)] + AUSSERHALB]
    eintraege.sort(key=lambda e: -len(e[1]))
    block = 'MARKEN = [\n' + ''.join("    (%r, r'%s'),\n" % e for e in eintraege) + ']\n'
    # Ende der Liste strukturell suchen: die erste Zeile, die nur aus ']'
    # besteht. Ein Markenname als Anker waere fragil - die Namen sind genau
    # das, was dieses Skript vorher ersetzt hat.
    a = t.index('MARKEN = [')
    b = t.index('\n]\n', a) + 3
    t = t[:a] + block + t[b:]
    raster = sorted({MARKEN[c][0] for c in MARKEN if MARKEN[c][1] or MARKEN[c][2]})
    t = re.sub(r'IM_RASTER = \{[^}]*\}',
               'IM_RASTER = {' + ', '.join(repr(n) for n in raster) + '}', t, count=1)
    io.open(pfad, 'w', encoding='utf-8').write(t)

    # synthetik.py uebernimmt die Kopfzeilen aus den Exporten der Vorlage.
    # Wo die liegen und wie die Vorlagenmarke heisst, kommt ueber die
    # Umgebung - so steht in synthetik.py selbst kein realer Name.
    umgebung = dict(os.environ, VORLAGE_EXPORT_2026=EXPORT_2026,
                    VORLAGE_EXPORT_2022=EXPORT_2022,
                    VORLAGE_MARKE=VORLAGE_MARKE,
                    VORLAGE_SEGMENTSPALTE=SEGMENTSPALTE,
                    ALTWELLE=ALTWELLE, VORLAGE_QUELLE=QUELLE)

    def lauf(s, pdf=False):
        argv = [sys.executable, s + '.py'] + (['--pdf'] if pdf else [])
        return subprocess.run(argv, cwd=ZIEL, capture_output=True, text=True,
                              env=umgebung)
    for s in ('qsf_demo', 'synthetik'):
        r = lauf(s)
        if r.returncode:
            raise SystemExit('%s fehlgeschlagen:\n%s' % (s, r.stderr[-900:]))
        print(r.stdout.strip().splitlines()[-1])
    # Rohdaten und Fragebogen entstehen erst jetzt und tragen die Kopfzeilen
    # und Fragetexte der Vorlage. Dieselbe Pruefung wie beim Kopieren.
    for muster in ('ZINTO_*.csv', 'ZINTO_*.qsf', ALTWELLE + '/*.csv'):
        for pfad in sorted(glob.glob(os.path.join(ZIEL, muster))):
            roh = io.open(pfad, encoding='utf-8').read().lower()
            uebrig = [w for w in VERBOTEN if w in roh]
            if uebrig:
                raise SystemExit(
                    '%s: Kategoriebegriffe stehen noch in den Daten (%s). Die '
                    'Fragetexte gehoeren in FRAGETEXTE von synthetik.py.'
                    % (os.path.basename(pfad), ', '.join(uebrig)))
    for s in SCHRITTE:
        # Die Decks gleich als PDF mitrendern - sie sind das, was weitergegeben
        # wird, und ein HTML ohne passendes PDF faellt sonst erst spaeter auf.
        r = lauf(s, pdf=s.startswith('slides_'))
        if r.returncode:
            raise SystemExit('%s fehlgeschlagen:\n%s' % (s, r.stderr[-900:]))
    print('Fertig in %s' % ZIEL)


if __name__ == '__main__':
    main()

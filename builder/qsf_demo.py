# -*- coding: utf-8 -*-
"""Erzeugt die Fragebogendateien der Fallstudie aus denen der echten Studie.

Ersetzt werden ausschliesslich die Markennamen und der Markenname im
Fragetext. Struktur, Logik, Exportcodes und Randomisierung bleiben
unveraendert - die Pipeline soll denselben Fragebogen sehen, nur mit anderen
Etiketten.
"""
import io, json, os, re, sys

from marken_demo import MARKEN, HELD_NAME
# Die Fragetexte und der Markenname der Vorlage stehen in vorlage.py und nur
# dort; dieses Skript nennt sie nicht.
from vorlage import QUELLE, QSF, FRAGETEXTE, SEGMENTSPALTE
from vorlage import MARKE as VORLAGE_MARKE

ECHT = {land: os.path.join(QUELLE, QSF % land) for land in ('AT', 'DE')}
AUS = {'AT': 'ZINTO_AT_Sep2026.qsf', 'DE': 'ZINTO_DE_Sep2026.qsf'}
RASTER = ('bekanntheit', 'betracht', 'kauf_3monate')


def namen_der_echten_studie(q):
    """Code -> echter Markenname, aus dem Bekanntheitsraster gelesen."""
    for e in q['SurveyElements']:
        p = e.get('Payload')
        if e['Element'] == 'SQ' and isinstance(p, dict) \
                and p.get('DataExportTag') == 'bekanntheit':
            rc = p['RecodeValues']
            return {rc[str(k)]: re.sub('<[^>]+>', '', p['Choices'][str(k)]['Display'])
                    for k in p['ChoiceOrder']}
    raise SystemExit('bekanntheit nicht gefunden')


def main():
    for land, pfad in ECHT.items():
        q = json.load(io.open(pfad, encoding='utf-8'))
        echt = namen_der_echten_studie(q)
        # 1  Markenetiketten in den drei Rastern tauschen
        getauscht = 0
        for e in q['SurveyElements']:
            p = e.get('Payload')
            if not (e['Element'] == 'SQ' and isinstance(p, dict)):
                continue
            if p.get('DataExportTag') not in RASTER:
                continue
            rc = p.get('RecodeValues') or {}
            for k, ch in p['Choices'].items():
                code = rc.get(str(k), str(k))
                if code in MARKEN:
                    ch['Display'] = MARKEN[code][0]
                    getauscht += 1
        # 2  Markenname im Fliesstext des Fragebogens
        roh = json.dumps(q, ensure_ascii=False)
        for code, name in sorted(echt.items(), key=lambda t: -len(t[1])):
            if code in MARKEN:
                roh = roh.replace(name, MARKEN[code][0])
        roh = roh.replace(VORLAGE_MARKE, HELD_NAME)
        # 3  Kategorie- und Institutsnennungen im Fragetext
        for a, b in FRAGETEXTE:
            roh = roh.replace(a, b)
        # Die Segmentvariable misst in der Fallstudie Clean Label; ihr
        # Exportname wandert mit, damit Fragebogen und Rohdaten dasselbe
        # Feld benennen.
        roh = re.sub(r'(?<![\w])' + SEGMENTSPALTE + r'(?![\w])',
                     'clean', roh)
        q = json.loads(roh)
        # Ein Code, den MARKEN nicht kennt, behaelt sein echtes Etikett -
        # und steht damit im Fragebogen und in allen Pruefprotokollen, die
        # die Marken von dort lesen. Das muss hier auffallen.
        erlaubt = {MARKEN[c][0] for c in MARKEN} | {'KEINE Marke'}
        for e in q['SurveyElements']:
            pl = e.get('Payload')
            if not (e['Element'] == 'SQ' and isinstance(pl, dict)):
                continue
            if pl.get('DataExportTag') not in RASTER:
                continue
            offen = sorted({re.sub('<[^>]+>', '', ch['Display'])
                            for ch in pl['Choices'].values()} - erlaubt)
            if offen:
                raise SystemExit(
                    '%s, %s: Etiketten ohne fiktive Entsprechung: %s - '
                    'MARKEN in marken_demo.py ergaenzen.'
                    % (land, pl['DataExportTag'], ', '.join(offen)))
        q['SurveyEntry']['SurveyName'] = \
            '%s Markenstudie %s (Demonstrationsdaten)' % (HELD_NAME, land)
        io.open(AUS[land], 'w', encoding='utf-8').write(
            json.dumps(q, ensure_ascii=False, indent=1))
        print('%s: %d Etiketten getauscht -> %s' % (land, getauscht, AUS[land]))


if __name__ == '__main__':
    main()

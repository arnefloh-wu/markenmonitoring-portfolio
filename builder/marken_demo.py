# -*- coding: utf-8 -*-
"""Fiktive Marken und Kategoriebegriffe fuer den Demonstrationsdatensatz.

ALLE Namen sind frei erfunden. Sie sind bewusst kategorieneutral gewaehlt:
Die Fallstudie zeigt eine Methode fuer Marken des taeglichen Bedarfs (FMCG)
und soll nicht nach einer bestimmten Warengruppe klingen. Keiner der Namen
entspricht einer realen Marke.

Die Codes entsprechen dem Raster der echten Studie, damit die Pipeline
unveraendert laeuft: 1-20 plus 90-92 landesspezifisch, 99 die Ausweichoption.
"""

# Code -> (Name, in AT im Raster, in DE im Raster)
MARKEN = {
    '1':  ('Avelio',      1, 1),
    '2':  ('Nutrika',     1, 1),
    '3':  ('Carelux',     1, 1),
    '4':  ('Granova',     1, 1),
    '5':  ('Alpenklar',   1, 0),   # nur AT, wie eine lokale Traditionsmarke
    '6':  ('Veranto',     1, 1),
    '7':  ('Purlino',     1, 0),   # nur AT
    '8':  ('Silvano',     1, 1),
    '9':  ('Frischal',    1, 1),
    '10': ('Almkraft',    1, 1),   # AT-Traditionsmarke, in DE schwach
    '11': ('Orbix',       1, 1),
    '12': ('Lunara',      1, 1),
    '13': ('ZINTO',       1, 1),   # die Marke der Fallstudie
    '14': ('Nordfit',     1, 1),
    '15': ('Clarivo',     1, 1),
    '16': ('Snapup',      1, 1),
    '17': ('Levito',      1, 1),
    '18': ('Protera',     1, 1),
    '19': ('Nutriq',      1, 1),
    '20': ('Sportlab',    1, 0),   # nur AT
    '90': ('Norvita',     0, 1),   # nur DE
    '91': ('Purelia',     0, 1),   # nur DE
    '92': ('Zweiklang',   0, 1),   # nur DE
    # Vier weitere deutsche Marken stehen im Fragebogen, aber nicht in der
    # Felddatei: Der Demonstrationsdatensatz nutzt fuer beide Laender dasselbe
    # Spaltenraster. Sie brauchen trotzdem fiktive Namen, sonst stehen sie mit
    # ihrem echten Namen im Fragebogen und in den Pruefprotokollen.
    '93': ('Helvano',     0, 0),
    '94': ('Ostfeld',     0, 0),
    '95': ('Taviro',      0, 0),
    '96': ('Lumio',       0, 0),
}
HELD = '13'
HELD_NAME = 'ZINTO'

# Marken, die im Raster 2022 standen (18 Stueck, wie in der echten Welle)
MARKEN_2022 = ['1','2','3','4','5','20','6','7','8','9','10','11','12','13',
               '14','15','16','17']

# Marken, die nur im freien Text auftauchen - das Gegenstueck zu den Marken,
# die nachtraeglich ins Raster aufgenommen wurden.
AUSSERHALB = ['Marvio', 'Terralu', 'Oskari', 'Weitfeld', 'Novalu',
              'Kernvoll', 'Saluta']

# Eigenmarken und Haendlernennungen, die in offenen Antworten vorkommen
RAUSCHEN = ['Eigenmarken', 'Supermarkt-Eigenmarke', 'weiss nicht', 'keine',
            'Bio-Laden', 'Drogerie']

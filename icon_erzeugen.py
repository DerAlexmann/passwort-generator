"""Erzeugt das Programmsymbol passwort_generator.ico.

Gezeichnet wird ein Vorhaengeschloss in Weiss auf einer abgerundeten Flaeche
im Akzentblau des Farbschemas. Die .ico enthaelt alle ueblichen Groessen, vom
Reiter der Taskleiste bis zur grossen Kachel im Explorer.

Aufruf:  python icon_erzeugen.py
Benoetigt:  pip install Pillow
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "passwort_generator.ico")
KANTE = 1024                                  # Vorlage, wird heruntergerechnet
GROESSEN = [16, 24, 32, 48, 64, 128, 256]

BLAU = (47, 125, 225, 255)                    # ACCENT des hellen Schemas
WEISS = (255, 255, 255, 255)


def zeichnen() -> Image.Image:
    bild = Image.new("RGBA", (KANTE, KANTE), (0, 0, 0, 0))
    stift = ImageDraw.Draw(bild)

    rand = KANTE // 16
    stift.rounded_rectangle((rand, rand, KANTE - rand, KANTE - rand),
                            radius=KANTE // 5, fill=BLAU)

    # Buegel: ein Halbkreis, dessen Enden im Korpus verschwinden
    dicke = KANTE // 12
    breite = KANTE // 3
    mitte = KANTE // 2
    oben = KANTE // 4
    stift.arc((mitte - breite // 2, oben, mitte + breite // 2, oben + breite),
              start=180, end=360, fill=WEISS, width=dicke)
    for seite in (-1, 1):
        x = mitte + seite * (breite // 2 - dicke // 2)
        stift.rectangle((x - dicke // 2, oben + breite // 2, x + dicke // 2, oben + breite),
                        fill=WEISS)

    # Korpus
    korpus = (mitte - KANTE // 4, oben + breite // 2 + dicke // 2,
              mitte + KANTE // 4, KANTE - KANTE // 4)
    stift.rounded_rectangle(korpus, radius=KANTE // 20, fill=WEISS)

    # Schluesselloch
    loch_mitte = (korpus[1] + korpus[3]) // 2
    r = KANTE // 20
    stift.ellipse((mitte - r, loch_mitte - r - r // 2, mitte + r, loch_mitte + r - r // 2),
                  fill=BLAU)
    stift.polygon([(mitte - r // 2, loch_mitte), (mitte + r // 2, loch_mitte),
                   (mitte + r, loch_mitte + 2 * r), (mitte - r, loch_mitte + 2 * r)],
                  fill=BLAU)
    return bild


def main() -> None:
    vorlage = zeichnen()
    vorlage.save(ZIEL, sizes=[(n, n) for n in GROESSEN])
    print("geschrieben:", ZIEL)


if __name__ == "__main__":
    main()

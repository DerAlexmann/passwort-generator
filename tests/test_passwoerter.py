"""Die Passworterzeugung - ohne Oberfläche, läuft überall."""

from __future__ import annotations

import math

import pytest

ALLE = ("gross", "klein", "ziffern", "sonder")


def test_laenge_stimmt(pg):
    for laenge in (4, 5, 16, 63, 64):
        assert len(pg.passwort_erzeugen(laenge, list(pg.ZEICHENGRUPPEN))) == laenge


def test_nur_gewaehlte_zeichen(pg):
    for gruppe in pg.ZEICHENGRUPPEN:
        passwort = pg.passwort_erzeugen(30, [gruppe])
        assert set(passwort) <= set(gruppe.zeichen)


def test_jede_gruppe_kommt_vor(pg):
    """Auch bei der kürzesten Länge, die gerade noch für alle Gruppen reicht."""
    gruppen = list(pg.ZEICHENGRUPPEN)
    for _wiederholung in range(200):
        passwort = pg.passwort_erzeugen(len(gruppen), gruppen)
        for gruppe in gruppen:
            assert any(zeichen in gruppe.zeichen for zeichen in passwort), passwort


def test_kurzer_als_gruppen_bleibt_gueltig(pg):
    """Reicht die Länge nicht für jede Gruppe, kommt trotzdem ein Passwort heraus."""
    gruppen = list(pg.ZEICHENGRUPPEN)
    passwort = pg.passwort_erzeugen(2, gruppen)
    assert len(passwort) == 2
    assert set(passwort) <= set(pg.vorrat_bilden(gruppen))


def test_ohne_gruppe_fehler(pg):
    with pytest.raises(ValueError):
        pg.passwort_erzeugen(8, [])


def test_reihenfolge_ist_gemischt(pg):
    """Das erste Zeichen darf nicht immer aus der ersten Gruppe stammen."""
    gruppen = list(pg.ZEICHENGRUPPEN)
    erste = {pg.passwort_erzeugen(8, gruppen)[0] for _wiederholung in range(200)}
    assert not erste <= set(gruppen[0].zeichen)


def test_vorrat_wird_ausgeschoepft(pg):
    gruppen = list(pg.ZEICHENGRUPPEN)
    vorrat = pg.vorrat_bilden(gruppen)
    gesehen = set()
    for _wiederholung in range(500):
        gesehen.update(pg.passwort_erzeugen(20, gruppen))
    assert gesehen == set(vorrat)


def test_passwoerter_wiederholen_sich_nicht(pg):
    gruppen = list(pg.ZEICHENGRUPPEN)
    erzeugt = {pg.passwort_erzeugen(16, gruppen) for _wiederholung in range(200)}
    assert len(erzeugt) == 200


@pytest.mark.parametrize("laenge, schluessel, stufe", [
    # Alle vier Gruppen - dieselben Grenzen wie vor der Umstellung auf Bit.
    (4, ALLE, "schwach"), (8, ALLE, "schwach"), (9, ALLE, "mittel"),
    (10, ALLE, "mittel"), (11, ALLE, "stark"), (64, ALLE, "stark"),
    # Kleiner Zeichenvorrat: dieselbe Laenge wiegt weniger.
    (11, ("ziffern",), "schwach"),               # 37 Bit
    (16, ("ziffern",), "schwach"),               # 53 Bit
    (17, ("ziffern",), "mittel"),                # 56 Bit
    (22, ("ziffern",), "stark"),                 # 73 Bit
    (11, ("klein",), "schwach"),                 # 52 Bit
    (12, ("klein",), "mittel"),                  # 56 Bit
    (15, ("klein",), "stark"),                   # 71 Bit
])
def test_staerkestufen(pg, laenge, schluessel, stufe):
    gruppen = [g for g in pg.ZEICHENGRUPPEN if g.schluessel in schluessel]
    assert pg.staerke_stufe(pg.staerke_bits(laenge, gruppen)) == stufe


def test_bits_sind_laenge_mal_vorrat(pg):
    """staerke_bits ist die Länge mal dem Logarithmus des Zeichenvorrats."""
    for schluessel in (("ziffern",), ("gross", "klein"), ALLE):
        gruppen = [g for g in pg.ZEICHENGRUPPEN if g.schluessel in schluessel]
        vorrat = len(pg.vorrat_bilden(gruppen))
        for laenge in (pg.MIN_LAENGE, 12, pg.MAX_LAENGE):
            assert pg.staerke_bits(laenge, gruppen) == pytest.approx(
                laenge * math.log2(vorrat))


def test_weniger_gruppen_bedeuten_weniger_bit(pg):
    """Gleiche Länge, kleinerer Vorrat: das Urteil muss nachgeben."""
    alle = list(pg.ZEICHENGRUPPEN)
    ziffern = [g for g in alle if g.schluessel == "ziffern"]
    assert pg.staerke_bits(12, ziffern) < pg.staerke_bits(12, alle)
    assert pg.staerke_stufe(pg.staerke_bits(12, alle)) == "stark"
    assert pg.staerke_stufe(pg.staerke_bits(12, ziffern)) == "schwach"


def test_ohne_zeichengruppe_keine_bits(pg):
    """Ohne Haken gibt es nichts zu bewerten - und keinen Rechenfehler."""
    assert pg.staerke_bits(16, []) == 0.0
    assert pg.staerke_stufe(pg.staerke_bits(16, [])) == "schwach"


def test_staerkefarben(pg):
    assert pg.STAERKE_ROLLE["schwach"] == "DANGER"
    assert pg.STAERKE_ROLLE["mittel"] == "WARN"
    assert pg.STAERKE_ROLLE["stark"] == "OK"
    for schema in pg.THEMES.values():
        for rolle in pg.STAERKE_ROLLE.values():
            assert schema[rolle].startswith("#")


def test_grenzen(pg):
    assert (pg.MIN_LAENGE, pg.MAX_LAENGE) == (4, 64)
    assert pg.VORGABE_LAENGE == pg.MIN_LAENGE
    assert 0 < pg.SCHWACH_BIS_BIT < pg.MITTEL_BIS_BIT < pg.BALKEN_VOLL_BIT


def test_zeichengruppen_ueberschneiden_sich_nicht(pg):
    gesehen: set[str] = set()
    for gruppe in pg.ZEICHENGRUPPEN:
        assert gruppe.zeichen, gruppe.schluessel
        assert not gesehen & set(gruppe.zeichen), gruppe.schluessel
        gesehen |= set(gruppe.zeichen)

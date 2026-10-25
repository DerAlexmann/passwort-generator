"""Die Passworterzeugung - ohne Oberfläche, läuft überall."""

from __future__ import annotations

import math
import string

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


@pytest.mark.parametrize("passwort, vorrat", [
    ("", 0),
    ("12345", 10),                               # nur Ziffern
    ("geheim", 26),                              # nur Kleinbuchstaben
    ("Geheim", 52),                              # dazu Großbuchstaben
    ("Geheim1", 62),                             # dazu Ziffern
    ("Geheim1!", 62 + len(string.punctuation)),  # alle vier Gruppen
    ("Käse", 53),                                # 26 + 26, das ä zählt einzeln
    ("äöü", 3),                                  # keine Gruppe getroffen
    ("!", len(string.punctuation)),              # Sonderzeichen allein
    ("a b", 27),                                 # das Leerzeichen zählt einzeln
    ("a\nb", 27),                                # ein eingefügter Umbruch auch
    ("ääää", 1),                                 # vier gleiche: ein Zeichen Vorrat
])
def test_vorrat_wird_aus_den_zeichen_geschaetzt(pg, passwort, vorrat):
    assert pg.vorrat_schaetzen(passwort) == vorrat


def test_vorrat_zaehlt_jede_gruppe_nur_einmal(pg):
    """Zehn Ziffern bleiben zehn Ziffern, auch wenn neun davon vorkommen."""
    assert pg.vorrat_schaetzen("1") == pg.vorrat_schaetzen("1234567890")
    assert pg.vorrat_schaetzen("aaaaaa") == pg.vorrat_schaetzen("abcdef")


def test_unbekannte_zeichen_werden_vorsichtig_bewertet(pg):
    """Über Zeichen außerhalb der vier Gruppen lässt sich nichts behaupten.

    Sie zählen deshalb einzeln statt als Gruppe - lieber zu wenig Bit als
    zu viele. Vier gleiche Umlaute sind damit ein Vorrat von einem Zeichen
    und null Bit, während "aaaa" über die Gruppe der Kleinbuchstaben auf 19
    Bit kommt. Die Zahl ist eine Obergrenze; nach unten darf sie irren.
    """
    assert pg.geschaetzte_bits("ääää") == 0.0
    assert pg.geschaetzte_bits("ääää") < pg.geschaetzte_bits("aaaa")
    assert pg.vorrat_schaetzen("абвгде") == 6        # je Zeichen eines


@pytest.mark.parametrize("laenge, vorrat, bits", [
    (0, 94, 0.0),                                # nichts eingegeben
    (12, 0, 0.0),                                # kein Vorrat
    (12, 1, 0.0),                                # ein einziges Zeichen: kein Zufall
    (1, 2, 1.0),                                 # ein Bit ist eine Münze
    (8, 2, 8.0),
    (10, 1024, 100.0),
])
def test_bits_zaehlen(pg, laenge, vorrat, bits):
    assert pg.bits_zaehlen(laenge, vorrat) == pytest.approx(bits)


def test_erzeugtes_passwort_wird_genauso_bewertet(pg):
    """Was der Generator auswirft, muss die Prüfung gleich bewerten.

    Das ist kein Zufallstest: Jede angehakte Gruppe kommt mindestens einmal
    vor, solange die Länge reicht - der geschätzte Vorrat trifft dann genau
    den tatsächlichen.
    """
    gruppen = list(pg.ZEICHENGRUPPEN)
    for laenge in (len(gruppen), 16, pg.MAX_LAENGE):
        passwort = pg.passwort_erzeugen(laenge, gruppen)
        assert pg.geschaetzte_bits(passwort) == pytest.approx(
            pg.staerke_bits(laenge, gruppen)), passwort


def test_eingabe_wird_wie_erzeugtes_passwort_gemessen(pg):
    """Dieselbe Rechnung: 12 Ziffern sind hier wie dort 40 Bit."""
    ziffern = [g for g in pg.ZEICHENGRUPPEN if g.schluessel == "ziffern"]
    assert pg.geschaetzte_bits("123456789012") == pytest.approx(
        pg.staerke_bits(12, ziffern))
    assert pg.staerke_stufe(pg.geschaetzte_bits("123456789012")) == "schwach"


@pytest.mark.parametrize("passwort, stufe", [
    ("", "schwach"),
    ("a", "schwach"),
    ("123456789012345678901", "mittel"),         # 21 Ziffern, 70 Bit
    ("1234567890123456789012", "stark"),         # 22 Ziffern, 73 Bit
    ("Geheim1!", "schwach"),                     # 8 Zeichen, 52 Bit
    ("Geheim12!", "mittel"),                     # 9 Zeichen, 59 Bit
    ("Geheim123!!", "stark"),                    # 11 Zeichen, 72 Bit
])
def test_stufen_einer_eingabe(pg, passwort, stufe):
    assert pg.staerke_stufe(pg.geschaetzte_bits(passwort)) == stufe


def test_laengere_eingabe_bringt_mehr_bit(pg):
    """Mehr Zeichen aus demselben Vorrat heißt mehr Zufall."""
    assert pg.geschaetzte_bits("abc") < pg.geschaetzte_bits("abcd")
    assert pg.geschaetzte_bits("abcd") < pg.geschaetzte_bits("abcD")


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

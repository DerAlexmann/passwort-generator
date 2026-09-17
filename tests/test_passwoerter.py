"""Die Passworterzeugung - ohne Oberfläche, läuft überall."""

from __future__ import annotations

import pytest


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


@pytest.mark.parametrize("laenge, stufe", [
    (4, "schwach"), (8, "schwach"), (9, "mittel"), (10, "mittel"), (11, "stark"), (64, "stark"),
])
def test_staerkestufen(pg, laenge, stufe):
    assert pg.staerke_stufe(laenge) == stufe


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
    assert pg.MIN_LAENGE <= pg.SCHWACH_BIS < pg.MITTEL_BIS < pg.MAX_LAENGE


def test_zeichengruppen_ueberschneiden_sich_nicht(pg):
    gesehen: set[str] = set()
    for gruppe in pg.ZEICHENGRUPPEN:
        assert gruppe.zeichen, gruppe.schluessel
        assert not gesehen & set(gruppe.zeichen), gruppe.schluessel
        gesehen |= set(gruppe.zeichen)

"""Die Sprachtabelle - vollständig, mit passenden Platzhaltern, ohne Karteileichen."""

from __future__ import annotations

import ast
import re

from conftest import PROGRAMMDATEI


def schluessel_im_quelltext():
    """Alle Texte, die im Code mit _("...") übersetzt werden."""
    baum = ast.parse(PROGRAMMDATEI.read_text(encoding="utf-8"))
    gefunden = set()
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name)
                and knoten.func.id == "_" and knoten.args):
            erstes = knoten.args[0]
            if isinstance(erstes, ast.Constant) and isinstance(erstes.value, str):
                gefunden.add(erstes.value)
    return gefunden


def alle_schluessel(pg):
    """Feste Schlüssel aus dem Quelltext plus die zur Laufzeit gebildeten."""
    laufzeit = {gruppe.bezeichnung for gruppe in pg.ZEICHENGRUPPEN}
    laufzeit |= set(pg.STAERKE_TEXT.values())
    return schluessel_im_quelltext() | laufzeit


def test_jede_sprache_ist_vollstaendig(pg):
    erwartet = alle_schluessel(pg)
    for sprache, tabelle in pg.TRANSLATIONS.items():
        fehlend = sorted(schluessel for schluessel in erwartet if schluessel not in tabelle)
        assert not fehlend, f"{sprache}: {fehlend}"


def test_keine_karteileichen(pg):
    erwartet = alle_schluessel(pg)
    for sprache, tabelle in pg.TRANSLATIONS.items():
        ueberzaehlig = sorted(schluessel for schluessel in tabelle if schluessel not in erwartet)
        assert not ueberzaehlig, f"{sprache}: {ueberzaehlig}"


def test_platzhalter_bleiben_erhalten(pg):
    for sprache, tabelle in pg.TRANSLATIONS.items():
        for deutsch, uebersetzt in tabelle.items():
            assert (set(re.findall(r"{(\w+)}", deutsch))
                    == set(re.findall(r"{(\w+)}", uebersetzt))), f"{sprache}: {deutsch!r}"


def test_jede_sprache_hat_einen_namen(pg):
    for sprache in pg.TRANSLATIONS:
        assert sprache in pg.LANGUAGE_NAMES
    assert pg.SOURCE_LANGUAGE in pg.LANGUAGE_NAMES


def test_uebersetzer_faellt_auf_deutsch_zurueck(pg):
    uebersetzer = pg.Translator("en")
    unbekannt = "Ein Text, den niemand übersetzt hat"
    assert uebersetzer(unbekannt) == unbekannt


def test_uebersetzt_merkt_schluessel_und_werte(pg):
    uebersetzer = pg.Translator("en")
    text = uebersetzer("Passwort mit {anzahl} Zeichen erzeugt.").format(anzahl=12)
    assert text.schluessel == "Passwort mit {anzahl} Zeichen erzeugt."
    assert text.werte == {"anzahl": 12}
    assert "12" in text


def test_quellsprache_gibt_den_text_zurueck(pg):
    uebersetzer = pg.Translator(pg.SOURCE_LANGUAGE)
    assert uebersetzer("Länge") == "Länge"
    assert uebersetzer("Länge").schluessel == "Länge"


def test_verfuegbare_sprachen_beginnen_mit_der_quellsprache(pg):
    namen = list(pg.Translator().available())
    assert namen[0] == pg.SOURCE_LANGUAGE
    assert set(namen) == {pg.SOURCE_LANGUAGE, *pg.TRANSLATIONS}

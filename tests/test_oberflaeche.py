"""Die Oberfläche: Fenster, Umschalten, Bestätigung, Einstellungen.

Braucht einen Bildschirm; ohne Tkinter oder ohne Anzeige werden diese Tests
übersprungen (siehe die Vorrichtung `fenster` in conftest.py).
"""

from __future__ import annotations

import json

from conftest import farben_sammeln, texte_sammeln


def test_startgroesse_und_lage(pg, fenster):
    app = fenster.bauen()
    wurzel = app.master
    breite, hoehe = wurzel.winfo_width(), wurzel.winfo_height()
    rand_x, rand_y, platz_breite, platz_hoehe = app.arbeitsflaeche
    assert (wurzel.winfo_x(), wurzel.winfo_y()) == (
        rand_x + max(0, (platz_breite - breite) // 2),
        rand_y + max(0, (platz_hoehe - hoehe) // 2))
    assert wurzel.resizable() == (0, 0)


def test_regler_und_vorgaben(pg, fenster):
    app = fenster.bauen()
    assert (app.regler["from"], app.regler["to"]) == (float(pg.MIN_LAENGE), float(pg.MAX_LAENGE))
    assert app.regler["resolution"] == 1.0
    assert app.var_laenge.get() == pg.VORGABE_LAENGE
    assert app.var_passwort.get() == ""
    assert str(app.knopf_kopieren["state"]) == "disabled"


def test_erzeugen_und_kopieren(pg, fenster):
    app = fenster.bauen(laenge=16)
    app.erzeugen()
    passwort = app.var_passwort.get()
    assert len(passwort) == 16
    assert str(app.knopf_kopieren["state"]) == "normal"

    app.kopieren()
    assert app.master.clipboard_get() == passwort

    app.erzeugen()
    assert app.var_passwort.get() != passwort


def test_staerkeanzeige_folgt_der_laenge(pg, fenster):
    app = fenster.bauen()
    for laenge in (pg.MIN_LAENGE, pg.SCHWACH_BIS, pg.SCHWACH_BIS + 1, pg.MITTEL_BIS,
                   pg.MITTEL_BIS + 1, pg.MAX_LAENGE):
        app.var_laenge.set(laenge)
        app._laenge_geaendert(sichern=False)
        stufe = pg.staerke_stufe(laenge)
        farbe = pg.THEMES[pg.CURRENT_THEME][pg.STAERKE_ROLLE[stufe]]
        assert app.balken.rolle == pg.STAERKE_ROLLE[stufe]
        assert str(app.staerke_text.cget("fg")) == farbe
        assert app.var_zahl.get() == str(laenge)
    assert app.balken.anteil == 1.0


def test_ohne_zeichengruppe_kein_erzeugen(pg, fenster):
    app = fenster.bauen()
    for gruppe in pg.ZEICHENGRUPPEN:
        app.var_gruppen[gruppe.schluessel].set(False)
    app._auswahl_geaendert(sichern=False)
    assert str(app.knopf_neu["state"]) == "disabled"

    app.var_gruppen["ziffern"].set(True)
    app._auswahl_geaendert(sichern=False)
    assert str(app.knopf_neu["state"]) == "normal"
    app.erzeugen()
    assert app.var_passwort.get().isdigit()


def test_sprachwechsel_aendert_nur_die_texte(pg, fenster):
    app = fenster.bauen(laenge=16)
    app.erzeugen()
    vorher = app.master.geometry()
    reiter = app.reiter.index("current")

    app.sprache_setzen("en")
    assert app.master.geometry() == vorher
    assert app.reiter.index("current") == reiter
    assert len(app.var_passwort.get()) == 16

    umgeschaltet = texte_sammeln(app)
    frisch_app, zuruecksetzen = fenster.vergleich("en", "light", laenge=16)
    frisch_app.erzeugen()
    frisch = texte_sammeln(frisch_app)
    zuruecksetzen()
    assert umgeschaltet == frisch


def test_schemawechsel_faerbt_nur_um(pg, fenster):
    app = fenster.bauen(laenge=16)
    app.erzeugen()
    vorher = app.master.geometry()

    app.var_dunkel.set(True)
    app._schema_umgeschaltet()
    assert app.master.geometry() == vorher
    assert pg.CURRENT_THEME == "dark"

    umgefaerbt = farben_sammeln(app)
    frisch_app, zuruecksetzen = fenster.vergleich("de", "dark", laenge=16)
    frisch_app.erzeugen()
    frisch = farben_sammeln(frisch_app)
    zuruecksetzen()
    assert umgefaerbt == frisch


def test_fenster_passt_in_jede_sprache(pg, fenster):
    """Die Startgröße muss den Bedarf jeder Sprache decken."""
    app = fenster.bauen()
    breite, hoehe = app.master.winfo_width(), app.master.winfo_height()
    for sprache in pg.Translator().available():
        vergleichs_app, zuruecksetzen = fenster.vergleich(sprache, "light")
        gebraucht = (vergleichs_app.master.winfo_reqwidth(),
                     vergleichs_app.master.winfo_reqheight())
        zuruecksetzen()
        assert gebraucht[0] <= breite and gebraucht[1] <= hoehe, sprache


def test_reiterwechsel_veraendert_das_fenster_nicht(pg, fenster):
    app = fenster.bauen()
    for sprache in ("de", "en"):
        app.sprache_setzen(sprache)
        vorher = app.master.geometry()
        for nummer in range(app.reiter.index("end")):
            app.reiter.select(nummer)
            app.master.update()
            assert app.master.geometry() == vorher, (sprache, nummer)
        app.reiter.select(0)


def test_bestaetigung_nach_dem_kopieren(pg, fenster):
    app = fenster.bauen(laenge=16)
    karte = app.hinweis.master
    hoehe_vorher = karte.winfo_reqheight()
    app.erzeugen()
    ruhig = str(app.hinweis.cget("bg"))

    app.kopieren()
    app.master.update()
    palette = pg.THEMES[pg.CURRENT_THEME]
    assert str(app.hinweis.cget("bg")) == palette["OK"]
    assert str(app.hinweis.cget("fg")) == palette["ON_ACCENT"]
    assert app.hinweis.cget("text").startswith("✓")
    assert app.bestaetigung_nachlauf is not None
    assert karte.winfo_reqheight() == hoehe_vorher      # das Layout bleibt ruhig

    app._bestaetigung_zurueck()
    app.master.update()
    assert str(app.hinweis.cget("bg")) == ruhig
    assert app.bestaetigung_nachlauf is None


def test_bestaetigung_uebersteht_sprach_und_schemawechsel(pg, fenster):
    app = fenster.bauen(laenge=16)
    app.erzeugen()
    app.kopieren()

    app.sprache_setzen("en")
    assert str(app.hinweis.cget("bg")) == pg.THEMES[pg.CURRENT_THEME]["OK"]
    assert app.hinweis.cget("text") == "✓   Copied to the clipboard."

    app.var_dunkel.set(True)
    app._schema_umgeschaltet()
    assert str(app.hinweis.cget("bg")) == pg.THEMES["dark"]["OK"]


def test_erzeugen_beendet_die_bestaetigung(pg, fenster):
    app = fenster.bauen(laenge=16)
    app.erzeugen()
    app.kopieren()
    app.erzeugen()
    assert app.bestaetigung_nachlauf is None
    assert str(app.hinweis.cget("bg")) == pg.THEMES[pg.CURRENT_THEME]["CARD"]


def test_einstellungen_werden_gesichert(pg, fenster, monkeypatch):
    app = fenster.bauen(laenge=24)
    gesichert = {}
    monkeypatch.setattr(pg, "save_config", lambda daten: gesichert.update(daten) or True)
    app.var_gruppen["sonder"].set(False)
    app._auswahl_geaendert(sichern=False)
    app._einstellungen_sichern(mit_fenster=True)

    assert set(gesichert) == {"language", "theme", "laenge", "zeichen", "fenster"}
    assert gesichert["laenge"] == 24
    assert gesichert["zeichen"]["sonder"] is False
    assert set(gesichert["fenster"]) == {"x", "y"}
    # Das Passwort selbst darf nirgends auftauchen.
    app.erzeugen()
    assert app.passwort not in json.dumps(gesichert)


def test_gespeicherte_einstellungen_kommen_zurueck(pg, fenster, monkeypatch):
    monkeypatch.setattr(pg, "load_config", lambda: {
        "language": "en", "theme": "dark", "laenge": 33,
        "zeichen": {"gross": True, "klein": False, "ziffern": True, "sonder": False}})
    app = fenster.bauen("en", "dark")
    assert app.var_laenge.get() == 33
    assert app.var_gruppen["klein"].get() is False
    assert app.var_gruppen["ziffern"].get() is True
    assert [g.schluessel for g in app.gewaehlte_gruppen()] == ["gross", "ziffern"]


def test_unsinnige_einstellungen_werden_gefangen(pg, fenster, monkeypatch):
    monkeypatch.setattr(pg, "load_config", lambda: {
        "laenge": 4000,
        "zeichen": {"gross": False, "klein": False, "ziffern": False, "sonder": False}})
    app = fenster.bauen()
    assert app.var_laenge.get() == pg.VORGABE_LAENGE
    assert app.gewaehlte_gruppen(), "ohne Gruppe ließe sich nichts erzeugen"


def test_fensterlage_ausserhalb_des_bildschirms_wird_zur_mitte(pg, fenster, monkeypatch):
    monkeypatch.setattr(pg, "load_config", lambda: {"fenster": {"x": 99999, "y": 99999}})
    app = fenster.bauen()
    wurzel = app.master
    breite, hoehe = wurzel.winfo_width(), wurzel.winfo_height()
    rand_x, rand_y, platz_breite, platz_hoehe = app.arbeitsflaeche
    assert (wurzel.winfo_x(), wurzel.winfo_y()) == (
        rand_x + max(0, (platz_breite - breite) // 2),
        rand_y + max(0, (platz_hoehe - hoehe) // 2))

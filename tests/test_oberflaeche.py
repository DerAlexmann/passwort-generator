"""Die Oberfläche: Fenster, Umschalten, Bestätigung, Einstellungen.

Braucht einen Bildschirm; ohne Tkinter oder ohne Anzeige werden diese Tests
übersprungen (siehe die Vorrichtung `fenster` in conftest.py).
"""

from __future__ import annotations

import json
import math

import pytest
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
    gruppen = app.gewaehlte_gruppen()
    for laenge in (pg.MIN_LAENGE, 8, 9, 10, 11, pg.MAX_LAENGE):
        app.var_laenge.set(laenge)
        app._laenge_geaendert(sichern=False)
        stufe = pg.staerke_stufe(pg.staerke_bits(laenge, gruppen))
        farbe = pg.THEMES[pg.CURRENT_THEME][pg.STAERKE_ROLLE[stufe]]
        assert app.balken.rolle == pg.STAERKE_ROLLE[stufe]
        assert str(app.staerke_text.cget("fg")) == farbe
        assert app.var_zahl.get() == str(laenge)
    assert app.balken.anteil == 1.0


def test_staerkeanzeige_folgt_dem_zeichenvorrat(pg, fenster):
    """Haken wegnehmen schwächt die Anzeige, obwohl die Länge bleibt."""
    app = fenster.bauen(laenge=12)
    assert app.staerke_stufe == "stark"
    voller_balken = app.balken.anteil

    for schluessel in ("gross", "klein", "sonder"):
        app.var_gruppen[schluessel].set(False)
    app._auswahl_geaendert(sichern=False)

    assert app.staerke_stufe == "schwach"          # 12 Ziffern sind 40 Bit
    assert round(app.staerke_bits) == 40
    assert app.balken.rolle == pg.STAERKE_ROLLE["schwach"]
    assert app.balken.anteil < voller_balken
    assert "40" in app.var_vorrat.get()
    assert "10" in app.var_vorrat.get()           # nur noch zehn Zeichen im Vorrat


def test_ohne_zeichengruppe_kein_erzeugen(pg, fenster):
    app = fenster.bauen()
    for gruppe in pg.ZEICHENGRUPPEN:
        app.var_gruppen[gruppe.schluessel].set(False)
    app._auswahl_geaendert(sichern=False)
    assert str(app.knopf_neu["state"]) == "disabled"

    assert app.balken.anteil == 0.0
    assert app.balken.balken.place_info() == {}, "kein Pixel Farbe ohne Zeichengruppe"

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


def test_pruefreiter_ist_vorhanden(pg, fenster):
    """Vier Reiter, „Prüfen“ an zweiter Stelle."""
    app = fenster.bauen()
    titel = [app.reiter.tab(nummer, "text").strip()
             for nummer in range(app.reiter.index("end"))]
    assert titel == ["Passwort", "Prüfen", "Erklärungen", "Info & Copyright"]


def test_pruefung_startet_leer(pg, fenster):
    app = fenster.bauen()
    assert app.var_pruefen.get() == ""
    assert app.var_pruef_staerke.get() == ""
    assert app.pruef_stufe is None
    assert app.pruef_balken.anteil == 0.0
    assert app.pruef_balken.balken.place_info() == {}, "kein Pixel Farbe ohne Eingabe"
    assert app.var_pruef_zahlen.get() == "Noch nichts eingegeben."
    assert str(app.pruef_text.cget("fg")) == pg.THEMES[pg.CURRENT_THEME]["TEXT"]


@pytest.mark.parametrize("passwort, stufe, bits, anteil, zeile", [
    ("123456789012", "schwach", 40, 0.40,
     "12 Zeichen · Vorrat 10 Zeichen · 40 Bit, wenn zufällig gewählt"),
    ("Geheim12!", "mittel", 59, 0.59,
     "9 Zeichen · Vorrat 94 Zeichen · 59 Bit, wenn zufällig gewählt"),
    ("Geheim123!!", "stark", 72, 0.72,
     "11 Zeichen · Vorrat 94 Zeichen · 72 Bit, wenn zufällig gewählt"),
    # Ab 100 Bit ist der Balken voll und bleibt es.
    ("Geheim123!!xxxxxxxxx", "stark", 131, 1.0,
     "20 Zeichen · Vorrat 94 Zeichen · 131 Bit, wenn zufällig gewählt"),
])
def test_pruefung_folgt_der_eingabe(pg, fenster, passwort, stufe, bits, anteil, zeile):
    """Die Anzeige wird beim Tippen mitgeführt, ohne Zutun von außen."""
    app = fenster.bauen()
    app.var_pruefen.set(passwort)
    app.master.update()
    rolle = pg.STAERKE_ROLLE[stufe]
    assert app.pruef_stufe == stufe
    assert round(app.pruef_bits) == bits
    assert app.pruef_balken.rolle == rolle
    assert round(app.pruef_balken.anteil, 2) == anteil
    # Tk gibt relwidth auf drei Stellen gerundet zurück.
    assert float(app.pruef_balken.balken.place_info()["relwidth"]) == pytest.approx(
        app.pruef_balken.anteil, abs=0.001)
    assert str(app.pruef_text.cget("fg")) == pg.THEMES[pg.CURRENT_THEME][rolle]
    assert app.var_pruef_staerke.get() == pg._(pg.STAERKE_TEXT[stufe])
    assert app.var_pruef_zahlen.get() == zeile


def test_sehr_lange_eingabe(pg, fenster):
    """Eingefügter Fließtext sprengt weder Anzeige noch Fenster."""
    app = fenster.bauen()
    vorher = app.master.geometry()
    app.var_pruefen.set("x" * 500)
    app.master.update()
    assert round(app.pruef_bits) == round(500 * math.log2(26))
    assert app.pruef_balken.anteil == 1.0
    assert app.master.geometry() == vorher


def test_pruefung_haengt_nicht_an_den_reglern(pg, fenster):
    """Länge und Haken des Generators gehen die Prüfung nichts an."""
    app = fenster.bauen(laenge=64)
    app.var_pruefen.set("12345")
    app.master.update()
    vorher = (app.pruef_bits, app.var_pruef_zahlen.get())

    app.var_laenge.set(8)
    app._laenge_geaendert(sichern=False)
    for schluessel in ("gross", "klein", "sonder"):
        app.var_gruppen[schluessel].set(False)
    app._auswahl_geaendert(sichern=False)

    assert (app.pruef_bits, app.var_pruef_zahlen.get()) == vorher
    # Umgekehrt lässt die Prüfung die Anzeige des Generators in Ruhe.
    staerke = (app.staerke_bits, app.balken.anteil, app.var_vorrat.get())
    app.var_pruefen.set("Geheim123!!")
    app.master.update()
    assert (app.staerke_bits, app.balken.anteil, app.var_vorrat.get()) == staerke


def test_feld_leeren(pg, fenster):
    app = fenster.bauen()
    app.var_pruefen.set("Geheim123!!")
    app.master.update()
    app.pruefung_leeren()
    app.master.update()
    assert app.var_pruefen.get() == ""
    assert app.pruef_stufe is None
    assert app.pruef_balken.anteil == 0.0
    assert app.pruef_balken.balken.place_info() == {}
    assert app.var_pruef_zahlen.get() == "Noch nichts eingegeben."


def test_strg_c_schweigt_auf_dem_pruefreiter(pg, fenster):
    """Auf dem Reiter „Prüfen“ kopiert Strg+C kein fremdes Passwort.

    Gerufen wird die Weiche selbst: Ein mit event_generate geschicktes
    Tastenereignis erreicht die Bindung am Fenster nicht verlässlich, weil Tk
    Tasten an das Widget mit dem Fokus gibt und ein Testfenster keinen hat.
    Dass die Taste am Fenster hängt, wird deshalb getrennt belegt.
    """
    app = fenster.bauen(laenge=16)
    assert app.master.bind("<Control-c>"), "Strg+C hängt am Fenster"
    app.erzeugen()
    app.master.clipboard_clear()
    app.master.clipboard_append("fremder Inhalt")
    app.var_pruefen.set("Geheim123!!")

    app.reiter.select(1)
    app.master.update()
    app._strg_c(None)
    assert app.master.clipboard_get() == "fremder Inhalt"
    assert app.var_status.get() != "In die Zwischenablage kopiert."
    assert not app.hinweis.cget("text").startswith("✓")

    app.reiter.select(0)
    app.master.update()
    app._strg_c(None)
    assert app.master.clipboard_get() == app.passwort


def test_eingegebenes_passwort_wird_nicht_gesichert(pg, fenster, monkeypatch):
    """Was im Prüffeld steht, darf in keiner Einstellung landen."""
    app = fenster.bauen()
    app.var_pruefen.set("Mein-echtes-Passwort-99!")
    app.master.update()
    gesichert = {}
    monkeypatch.setattr(pg, "save_config", lambda daten: gesichert.update(daten) or True)
    app._einstellungen_sichern(mit_fenster=True)

    assert set(gesichert) == {"language", "theme", "laenge", "zeichen", "fenster"}
    assert "Mein-echtes-Passwort-99!" not in json.dumps(gesichert)
    assert app.var_status.get() == "Bereit – „Neu generieren“ erzeugt das Passwort."


def test_fusszeile_gehoert_dem_generator(pg, fenster):
    """Der Zeichenvorrat unten rechts beschreibt den Generator, nicht die Prüfung."""
    app = fenster.bauen(laenge=16)
    assert app.var_vorrat.get() == "Zeichenvorrat: 94 Zeichen · 105 Bit"

    app.reiter.select(1)
    app.master.update()
    assert app.var_vorrat.get() == ""
    assert app.aktiver_reiter == 1

    app.var_pruefen.set("Geheim12!")               # die Prüfung füllt sie nicht
    app.sprache_setzen("en")                       # ein Sprachwechsel auch nicht
    app.master.update()
    assert app.var_vorrat.get() == ""

    app.reiter.select(0)
    app.master.update()
    assert app.var_vorrat.get() == "Character pool: 94 characters · 105 bits"


def test_pruefbefund_uebersteht_sprach_und_schemawechsel(pg, fenster):
    app = fenster.bauen()
    app.var_pruefen.set("Geheim12!")
    app.master.update()
    deutsch = (app.var_pruef_staerke.get(), app.var_pruef_zahlen.get())
    assert deutsch == ("Mittel",
                       "9 Zeichen · Vorrat 94 Zeichen · 59 Bit, wenn zufällig gewählt")

    app.sprache_setzen("en")
    assert app.var_pruef_staerke.get() == "Medium"
    assert app.var_pruef_zahlen.get() == ("9 characters · pool of 94 · 59 bits, "
                                          "if chosen at random")
    assert app.var_pruefen.get() == "Geheim12!"

    # Und zurück: Der gemerkte Text muss seinen Schlüssel behalten haben,
    # sonst bliebe er in der zweiten Sprache stehen.
    app.sprache_setzen("de")
    assert (app.var_pruef_staerke.get(), app.var_pruef_zahlen.get()) == deutsch

    for dunkel, schema in ((True, "dark"), (False, "light")):
        app.var_dunkel.set(dunkel)
        app._schema_umgeschaltet()
        assert str(app.pruef_text.cget("fg")) == pg.THEMES[schema]["WARN"]
        assert str(app.pruef_balken.balken.cget("bg")) == pg.THEMES[schema]["WARN"]


def test_anzeige_rechnet_wie_die_funktion(pg, fenster):
    """Die Oberfläche darf nicht anders rechnen als geschaetzte_bits()."""
    app = fenster.bauen()
    for passwort in ("", "a", "12345", "Käse", "ääää", "Geheim123!!", "x" * 200):
        app.var_pruefen.set(passwort)
        app.master.update()
        assert app.pruef_bits == pg.geschaetzte_bits(passwort), passwort
        if passwort:
            assert str(pg.vorrat_schaetzen(passwort)) in app.var_pruef_zahlen.get()

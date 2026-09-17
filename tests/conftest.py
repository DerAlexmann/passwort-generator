"""Gemeinsame Vorrichtungen für die Tests.

Das Programm ist eine einzelne `.pyw`-Datei und damit über den gewöhnlichen
Import nicht erreichbar; geladen wird es deshalb über einen SourceFileLoader.
Gespeichert wird in den Tests nichts: `load_config` und `save_config` sind
ersetzt, sodass keine Einstellungsdatei entsteht.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest

PROGRAMMDATEI = Path(__file__).resolve().parent.parent / "Passwort-Generator.pyw"


@pytest.fixture(scope="session")
def pg():
    """Das Programm als Modul."""
    lader = importlib.machinery.SourceFileLoader("passwort_generator", str(PROGRAMMDATEI))
    spec = importlib.util.spec_from_loader("passwort_generator", lader)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["passwort_generator"] = modul
    lader.exec_module(modul)
    modul.save_config = lambda daten: True
    modul.load_config = lambda: {}
    return modul


@pytest.fixture
def fenster(pg):
    """Baut Fenster der Anwendung und räumt sie hinterher weg.

    Die Farb- und Textverzeichnisse des Programms gelten für genau ein
    Fenster - `_aufbauen()` leert sie. Für Vergleiche mit einem frisch
    gebauten Fenster gibt es deshalb `vergleich()`, das die Verzeichnisse
    sichert und danach wiederherstellt.
    """
    tk = pytest.importorskip("tkinter", reason="Tkinter ist nicht verfügbar")
    from tkinter import ttk

    try:
        probe = tk.Tk()
    except tk.TclError as fehler:                # z. B. Linux-Läufer ohne Bildschirm
        pytest.skip(f"kein Bildschirm verfügbar: {fehler}")
    probe.destroy()

    pg._tk, pg._ttk = tk, ttk
    pg.widgets_bereitstellen()
    offen = []

    class Werkstatt:
        def bauen(self, sprache="de", schema="light", laenge=None):
            pg._.language = sprache
            pg.apply_theme(schema)
            wurzel = tk.Tk()
            app = pg.PasswortApp(wurzel)
            if laenge is not None:
                app.var_laenge.set(laenge)
                app._laenge_geaendert(sichern=False)
            wurzel.update()
            offen.append(wurzel)
            return app

        def vergleich(self, sprache, schema, laenge=None):
            """Frisches Fenster bauen, hergeben, danach den alten Zustand zurückholen."""
            gemerkt_farben = list(pg.GEFAERBTE_WIDGETS)
            gemerkt_texte = list(pg.BESCHRIFTUNGEN)
            schema_vorher, sprache_vorher = pg.CURRENT_THEME, pg._.language
            app = self.bauen(sprache, schema, laenge)

            def zuruecksetzen():
                app.master.destroy()
                offen.remove(app.master)
                pg.GEFAERBTE_WIDGETS[:] = gemerkt_farben
                pg.BESCHRIFTUNGEN[:] = gemerkt_texte
                pg.apply_theme(schema_vorher)
                pg._.language = sprache_vorher

            return app, zuruecksetzen

    yield Werkstatt()

    for wurzel in offen:
        try:
            wurzel.destroy()
        except tk.TclError:                      # war schon zu
            pass
    pg._.language = pg.SOURCE_LANGUAGE
    pg.apply_theme(pg.DEFAULT_THEME)


def texte_sammeln(app):
    """Alle festen Beschriftungen samt Reitern und Laufzeitwerten."""
    import tkinter as tk

    app.master.update()
    gesammelt = []

    def lauf(widget, pfad):
        try:
            if "text" in widget.keys() and not (
                    "textvariable" in widget.keys() and str(widget.cget("textvariable"))):
                gesammelt.append((pfad, str(widget.cget("text"))))
        except tk.TclError:                      # ttk-Eigenheit, etwa bei Entry
            pass
        for nummer, kind in enumerate(widget.winfo_children()):
            lauf(kind, f"{pfad}/{kind.winfo_class()}{nummer}")

    lauf(app.master, "")
    for nummer in range(app.reiter.index("end")):
        gesammelt.append((f"reiter{nummer}", app.reiter.tab(nummer, "text")))
    for name in ("var_status", "var_staerke", "var_vorrat", "var_zahl"):
        gesammelt.append((name, getattr(app, name).get()))
    return gesammelt


FARBOPTIONEN = ("bg", "fg", "troughcolor", "activebackground", "activeforeground",
                "highlightbackground", "highlightcolor", "selectcolor", "selectbackground",
                "selectforeground", "readonlybackground", "disabledbackground",
                "disabledforeground", "insertbackground")


def farben_sammeln(app):
    """Alle Farboptionen aller Widgets, dazu die zustandsabhängigen Farben."""
    import tkinter as tk

    app.master.update()
    gesammelt = []

    def lauf(widget, pfad):
        for option in FARBOPTIONEN:
            try:
                if option in widget.keys():
                    gesammelt.append((pfad, option, str(widget.cget(option))))
            except tk.TclError:
                pass
        for nummer, kind in enumerate(widget.winfo_children()):
            lauf(kind, f"{pfad}/{kind.winfo_class()}{nummer}")

    lauf(app.master, "")
    gesammelt.append(("balken", "bg", str(app.balken.balken.cget("bg"))))
    gesammelt.append(("staerketext", "fg", str(app.staerke_text.cget("fg"))))
    gesammelt.append(("hinweis", "bg", str(app.hinweis.cget("bg"))))
    return gesammelt

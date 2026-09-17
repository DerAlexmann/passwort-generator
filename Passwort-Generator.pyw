"""
Passwort-Generator 1.1.0 - sichere Passwoerter erzeugen und kopieren

Erzeugt Passwoerter aus den gewaehlten Zeichengruppen mit dem
Zufallsgenerator des Betriebssystems (secrets) und legt sie auf Wunsch in
die Zwischenablage; das Kopieren wird kurz gruen bestaetigt. Laenge,
Zeichenauswahl, Sprache, Farbschema und Fensterlage bleiben bis zum
naechsten Start erhalten.

Farbschema, Sprachumschaltung und Aufbau folgen dem uebrigen Hausstil.

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI

Benoetigt nur die Standardbibliothek (Tkinter gehoert dazu).
"""

from __future__ import annotations

import json
import locale
import os
import secrets
import string
import sys
from dataclasses import dataclass

PROGRAMM = "Passwort-Generator"
VERSION = "1.1.0"

# Von gui_starten() belegt, sobald Tkinter geladen ist.
_tk = None
_ttk = None


# --------------------------------------------------------------------------
# Farbschemata
#
# apply_theme() schreibt die Werte der gewaehlten Palette in die
# Modulvariablen - der uebrige Code benutzt einfach BG, CARD, TEXT ... und
# muss vom Umschalten nichts wissen. Ein eigenes Schema entsteht durch eine
# weitere Palette mit denselben Namen.
# --------------------------------------------------------------------------

THEMES = {
    "light": {
        "BG": "#eef1f5",             # Seitenhintergrund
        "CARD": "#ffffff",           # Karten
        "CARD_ALT": "#fbfcfe",       # Text- und Listenflaechen in Karten
        "BORDER": "#d7dce4",
        "TEXT": "#1b2430",
        "MUTED": "#6c7684",          # Nebentext
        "HEADER": "#1d2330",         # Kopfzeile mit Titel und Umschaltern
        "HEADER_TEXT": "#c2cad8",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#69748c",
        "HEADER_HOVER": "#2b3346",
        "ACCENT": "#2f7de1",
        "ACCENT_DARK": "#1f66c4",
        "ON_ACCENT": "#ffffff",      # Schrift auf farbigen Flaechen
        "OK": "#2e9e5b",
        "OK_DARK": "#25864b",
        "WARN": "#e08b1f",
        "WARN_DARK": "#c4770f",
        "DANGER": "#d64545",
        "DANGER_DARK": "#b83a3a",
        "BTN_BG": "#e3e8f0",         # unauffaelliger Schalter
        "BTN_HOVER": "#d2d9e6",
        "BTN_TEXT": "#1b2430",
        "BTN_DISABLED": "#9aa3b0",
        "FIELD_BG": "#ffffff",       # Eingabefelder
        "TROUGH": "#e3e8f0",         # Rille von Schiebereglern
        "TAB_BG": "#e3e8f0",         # nicht gewaehlter Reiter
        "STATUS_BG": "#e4e8ef",
    },
    "dark": {
        "BG": "#12161d",
        "CARD": "#1a1f28",
        "CARD_ALT": "#151a22",
        "BORDER": "#2c3441",
        "TEXT": "#e6eaf0",
        "MUTED": "#98a2b3",
        "HEADER": "#0e1218",
        "HEADER_TEXT": "#b8c2d0",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#6b7688",
        "HEADER_HOVER": "#212a38",
        "ACCENT": "#4a90e8",
        "ACCENT_DARK": "#3a7ad0",
        "ON_ACCENT": "#ffffff",
        "OK": "#3fb972",
        "OK_DARK": "#349b60",
        "WARN": "#e9a23b",
        "WARN_DARK": "#cc8a26",
        "DANGER": "#e05a5a",
        "DANGER_DARK": "#c44a4a",
        "BTN_BG": "#2a323f",
        "BTN_HOVER": "#353f4f",
        "BTN_TEXT": "#e6eaf0",
        "BTN_DISABLED": "#626c7a",
        "FIELD_BG": "#232b36",
        "TROUGH": "#2a323f",
        "TAB_BG": "#232b36",
        "STATUS_BG": "#0e1218",
    },
}

DEFAULT_THEME = "light"
CURRENT_THEME = DEFAULT_THEME


def apply_theme(name):
    """Farbwerte des gewaehlten Schemas in die Modulvariablen schreiben."""
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else DEFAULT_THEME
    globals().update(THEMES[CURRENT_THEME])


apply_theme(DEFAULT_THEME)      # legt BG, CARD, TEXT ... ueberhaupt erst an

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_PASSWORT = ("Consolas", 13)
FONT_ZAHL = ("Consolas", 12, "bold")


# --------------------------------------------------------------------------
# Sprachumschaltung
#
# Deutsch ist die Quellsprache: im Code steht der deutsche Text, _("...")
# sucht ihn zur Laufzeit in der Sprachtabelle TRANSLATIONS (ganz unten in
# dieser Datei). Dort ist auch beschrieben, wie eine weitere Sprache
# dazukommt.
# --------------------------------------------------------------------------

SOURCE_LANGUAGE = "de"
CONFIG_NAME = "passwort-generator.json"


class Uebersetzt(str):
    """Uebersetzter Text, der seinen deutschen Schluessel kennt.

    Verhaelt sich ueberall wie ein gewoehnlicher String. beschriften() liest
    daraus ab, wie sich eine Beschriftung nach einem Sprachwechsel neu bilden
    laesst - samt der Werte, die mit format() eingesetzt wurden.
    """

    def __new__(cls, text, schluessel, werte=None):
        neu = super().__new__(cls, text)
        neu.schluessel = schluessel
        neu.werte = werte or {}
        return neu

    def format(self, *args, **kwargs):
        if args:                             # Positionsargumente nutzt hier niemand
            return str.format(self, *args, **kwargs)
        return Uebersetzt(str.format(self, **kwargs), self.schluessel, kwargs)


class Translator:
    """Uebersetzt einen deutschen Quelltext in die eingestellte Sprache."""

    def __init__(self, language=SOURCE_LANGUAGE):
        self.language = language

    def __call__(self, text):
        if self.language == SOURCE_LANGUAGE:
            return Uebersetzt(text, text)
        return Uebersetzt(TRANSLATIONS.get(self.language, {}).get(text, text), text)

    def available(self):
        """Sprachkuerzel -> Anzeigename, Quellsprache immer zuerst."""
        names = {SOURCE_LANGUAGE: LANGUAGE_NAMES[SOURCE_LANGUAGE]}
        for code in TRANSLATIONS:
            names[code] = LANGUAGE_NAMES.get(code, code)
        return names


_ = Translator()


# --------------------------------------------------------------------------
# Einstellungen
# --------------------------------------------------------------------------

def ist_eingefroren() -> bool:
    """Laeuft das Programm als gebuendelte EXE (PyInstaller & Co.)?"""
    return getattr(sys, "frozen", False)


def programm_ordner() -> str:
    """Ordner, in dem das Programm fuer den Anwender sichtbar liegt.

    Als PyInstaller-EXE mit --onefile entpackt sich das Programm in einen
    temporaeren Ordner (sys._MEIPASS), den PyInstaller beim Beenden wieder
    loescht - __file__ zeigt dorthin. Alles, was den Programmlauf ueberdauern
    soll, gehoert deshalb neben die EXE und nicht neben __file__.
    """
    if ist_eingefroren():
        return os.path.dirname(os.path.abspath(sys.executable))
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:                       # z. B. interaktive Eingabe
        return os.path.expanduser("~")


def config_path():
    """Ablageort der Einstellungen - neben dem Programm."""
    return os.path.join(programm_ordner(), CONFIG_NAME)


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as datei:
            daten = json.load(datei)
        return daten if isinstance(daten, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(daten):
    try:
        with open(config_path(), "w", encoding="utf-8") as datei:
            json.dump(daten, datei, indent=2)
        return True
    except OSError:
        return False


def detect_language():
    """Sprache des Betriebssystems, falls dafuer eine Tabelle vorliegt."""
    try:
        locale.setlocale(locale.LC_CTYPE, "")
        code = (locale.getlocale()[0] or "").lower()
    except (locale.Error, ValueError):
        code = ""
    bekannt = {SOURCE_LANGUAGE, *TRANSLATIONS}
    kurz = code.split("_")[0]
    if kurz in bekannt:
        return kurz
    for name, sprache in (("german", "de"), ("deutsch", "de"), ("english", "en")):
        if kurz.startswith(name) and sprache in bekannt:
            return sprache
    return SOURCE_LANGUAGE


def startup_language():
    """Gespeicherte Sprache, sonst die des Betriebssystems."""
    gespeichert = load_config().get("language")
    if gespeichert and (gespeichert == SOURCE_LANGUAGE or gespeichert in TRANSLATIONS):
        return gespeichert
    return detect_language()


def startup_theme():
    """Gespeichertes Farbschema, sonst das helle."""
    gespeichert = load_config().get("theme")
    return gespeichert if gespeichert in THEMES else DEFAULT_THEME


# --------------------------------------------------------------------------
# Passwoerter
#
# Gewuerfelt wird mit secrets, also mit dem Zufallsgenerator des
# Betriebssystems. random waere vorhersagbar, sobald jemand ein paar
# Ergebnisse kennt, und hat in einem Passwortgenerator nichts zu suchen.
# --------------------------------------------------------------------------

MIN_LAENGE = 4
MAX_LAENGE = 64
VORGABE_LAENGE = MIN_LAENGE

# Grenzen der Staerkeanzeige: bis 8 rot, bis 10 gelb, darueber gruen.
SCHWACH_BIS = 8
MITTEL_BIS = 10


@dataclass(frozen=True)
class Zeichengruppe:
    """Eine ankreuzbare Gruppe von Zeichen."""

    schluessel: str          # Name in der Einstellungsdatei
    bezeichnung: str         # deutscher Text, zugleich Uebersetzungsschluessel
    zeichen: str


ZEICHENGRUPPEN = (
    Zeichengruppe("gross", "Großbuchstaben", string.ascii_uppercase),
    Zeichengruppe("klein", "Kleinbuchstaben", string.ascii_lowercase),
    Zeichengruppe("ziffern", "Ziffern", string.digits),
    Zeichengruppe("sonder", "Satz- und Sonderzeichen", string.punctuation),
)


def vorrat_bilden(gruppen) -> str:
    """Alle Zeichen der gewaehlten Gruppen hintereinander."""
    return "".join(gruppe.zeichen for gruppe in gruppen)


def passwort_erzeugen(laenge: int, gruppen) -> str:
    """Passwort der gewuenschten Laenge aus den gewaehlten Gruppen.

    Jede gewaehlte Gruppe kommt mindestens einmal vor, solange die Laenge
    dafuer reicht - sonst koennte ein Passwort mit Haken bei "Ziffern"
    zufaellig ganz ohne Ziffer herauskommen und von einer Anmeldemaske
    abgelehnt werden. Zum Schluss wird gemischt, damit die Reihenfolge der
    Gruppen nicht am Anfang des Passworts ablesbar ist.
    """
    if not gruppen:
        raise ValueError("Keine Zeichengruppe gewählt")
    vorrat = vorrat_bilden(gruppen)
    zeichen = [secrets.choice(gruppe.zeichen) for gruppe in gruppen][:laenge]
    zeichen += [secrets.choice(vorrat) for _rest in range(laenge - len(zeichen))]
    for i in range(len(zeichen) - 1, 0, -1):            # Fisher-Yates mit secrets
        j = secrets.randbelow(i + 1)
        zeichen[i], zeichen[j] = zeichen[j], zeichen[i]
    return "".join(zeichen)


def staerke_stufe(laenge: int) -> str:
    """Stufe der Staerkeanzeige: "schwach", "mittel" oder "stark"."""
    if laenge <= SCHWACH_BIS:
        return "schwach"
    if laenge <= MITTEL_BIS:
        return "mittel"
    return "stark"


STAERKE_ROLLE = {"schwach": "DANGER", "mittel": "WARN", "stark": "OK"}
STAERKE_TEXT = {"schwach": "Schwach", "mittel": "Mittel", "stark": "Stark"}


# --------------------------------------------------------------------------
# Bausteine der Oberflaeche
#
# faerben() merkt sich zu jedem Widget, welche Rolle seine Farben haben
# ("CARD", "TEXT", ...), beschriften() merkt sich den Uebersetzungsschluessel
# jeder Beschriftung. Sprache und Farbschema lassen sich dadurch umschalten,
# ohne die Oberflaeche neu aufzubauen - nichts blinkt, nichts springt.
# --------------------------------------------------------------------------

FlatButton = None

# (Widget, Rollen) - Rollen ist None bei Widgets, die sich selbst umfaerben.
GEFAERBTE_WIDGETS: list = []


def faerben(widget, **rollen):
    """Widget einfaerben und die Farbrollen fuer spaeteres Umfaerben merken.

    Beispiel:  faerben(label, bg="CARD", fg="TEXT")
    """
    GEFAERBTE_WIDGETS.append((widget, rollen))
    widget.configure(**{option: THEMES[CURRENT_THEME][name] for option, name in rollen.items()})
    return widget


def farben_auffrischen():
    """Alle gemerkten Widgets auf die aktuelle Palette umstellen.

    Zerstoerte Widgets fallen dabei aus der Liste heraus; Tk meldet sie mit
    einem TclError, was hier das Aufraeumkriterium ist.
    """
    palette = THEMES[CURRENT_THEME]
    uebrig = []
    for widget, rollen in GEFAERBTE_WIDGETS:
        try:
            if rollen is None:
                widget.neu_faerben()
            else:
                widget.configure(**{opt: palette[name] for opt, name in rollen.items()})
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((widget, rollen))
    GEFAERBTE_WIDGETS[:] = uebrig


# (Setzfunktion, Schluessel, Werte) - fuer den Sprachwechsel ohne Neuaufbau
BESCHRIFTUNGEN: list = []


def beschriftung_merken(setzen, text):
    """setzen(text) ausfuehren und - stammt der Text aus _() - fuer spaeter merken.

    Beim Sprachwechsel bildet texte_auffrischen() den Text aus demselben
    Schluessel in der neuen Sprache und ruft setzen() erneut auf.
    """
    setzen(text)
    if isinstance(text, Uebersetzt):
        BESCHRIFTUNGEN.append((setzen, text.schluessel, text.werte))


def beschriften(widget, text, option="text"):
    """Widget beschriften und den Text fuer den Sprachwechsel merken.

    Beispiel:  beschriften(label, _("Länge"))
    """
    beschriftung_merken(lambda neu: widget.configure(**{option: neu}), text)
    return widget


def texte_auffrischen():
    """Alle gemerkten Beschriftungen in die aktuelle Sprache bringen.

    Zerstoerte Widgets fallen - wie bei farben_auffrischen() - ueber den
    TclError aus der Liste heraus.
    """
    uebrig = []
    for setzen, schluessel, werte in BESCHRIFTUNGEN:
        text = _(schluessel)
        try:
            setzen(text.format(**werte) if werte else text)
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((setzen, schluessel, werte))
    BESCHRIFTUNGEN[:] = uebrig


def zeichnen_anhalten(fenster_id):
    """Haelt das Zeichnen eines Fensters samt Inhalt an; liefert die Fortsetzung.

    Tk zeichnet jedes Element einzeln auf den Bildschirm. Aendert sich beim
    Sprachwechsel die Beschriftung von zwei Dutzend Elementen, saehe man sonst
    jeden Zwischenstand. Mit WM_SETREDRAW laesst Windows das alte Bild stehen,
    bis alles fertig ist; danach wird in einem Zug neu gezeichnet.

    Die Fortsetzung muss auch im Fehlerfall laufen, sonst bliebe das Fenster
    eingefroren - der Aufruf gehoert deshalb in ein try/finally.
    """
    if sys.platform != "win32":
        return lambda: None
    try:
        import ctypes
        benutzer = ctypes.windll.user32
        benutzer.SendMessageW(fenster_id, 0x000B, 0, 0)      # WM_SETREDRAW aus
    except (AttributeError, OSError):
        return lambda: None

    def fortsetzen():
        benutzer.SendMessageW(fenster_id, 0x000B, 1, 0)      # WM_SETREDRAW an
        # RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW
        benutzer.RedrawWindow(fenster_id, None, None, 0x0001 | 0x0080 | 0x0100)
    return fortsetzen


def widgets_bereitstellen():
    """Definiert die Widget-Klassen, sobald Tkinter geladen ist."""
    global FlatButton

    class _FlatButton(_tk.Button):
        """Flacher Button mit Hover-Effekt in mehreren Farbvarianten."""

        @staticmethod
        def styles():
            """Farbvarianten - erst beim Aufruf gelesen, damit das Schema stimmt."""
            return {
                "primary":   (ACCENT, ACCENT_DARK, ON_ACCENT),
                "secondary": (BTN_BG, BTN_HOVER, BTN_TEXT),
                "success":   (OK, OK_DARK, ON_ACCENT),
                "warn":      (WARN, WARN_DARK, ON_ACCENT),
                "danger":    (DANGER, DANGER_DARK, ON_ACCENT),
            }

        def __init__(self, parent, text, command=None, kind="secondary", **kw):
            kw.setdefault("padx", 14)
            kw.setdefault("pady", 6)
            super().__init__(parent, text=text, command=command, relief="flat", bd=0,
                             highlightthickness=0, cursor="hand2", font=FONT_SMALL, **kw)
            self._kind = kind
            beschriften(self, text)                  # merkt sich uebersetzte Texte
            self.neu_faerben()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst

        def neu_faerben(self):
            """Farben der eigenen Variante aus der aktuellen Palette holen."""
            styles = self.styles()
            bg, hover, fg = styles.get(self._kind, styles["secondary"])
            self._bg, self._hover = bg, hover
            self.configure(bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                           disabledforeground=BTN_DISABLED)

        def _enabled(self):
            return str(self["state"]) != "disabled"

        def _on_enter(self, _e):
            if self._enabled():
                self.configure(bg=self._hover)

        def _on_leave(self, _e):
            self.configure(bg=self._bg)

    FlatButton = _FlatButton


def make_card(parent, **pack_kw):
    """Karte mit dünnem Rahmen."""
    card = faerben(_tk.Frame(parent, highlightthickness=1),
                   bg="CARD", highlightbackground="BORDER", highlightcolor="BORDER")
    if pack_kw:
        card.pack(**pack_kw)
    return card


def card_title(parent, text):
    etikett = beschriften(faerben(_tk.Label(parent, font=FONT_BOLD, anchor="w"),
                                  bg="CARD", fg="TEXT"), text)
    etikett.pack(fill="x", padx=14, pady=(12, 6))
    return etikett


def card_text(parent, text, rolle="MUTED", font=None, wraplength=620):
    """Fliesstext in einer Karte."""
    etikett = beschriften(faerben(
        _tk.Label(parent, font=font or FONT_SMALL, justify="left", anchor="w",
                  wraplength=wraplength),
        bg="CARD", fg=rolle), text)
    etikett.pack(fill="x", padx=14, pady=(0, 10))
    return etikett


class Staerkebalken:
    """Farbiger Balken, dessen Länge und Farbe die Passwortstärke zeigen.

    Die Farbe steckt nicht fest im Widget, sondern als Rolle ("DANGER",
    "WARN", "OK") - beim Wechsel des Farbschemas holt neu_faerben() die
    passende Farbe aus der neuen Palette.
    """

    def __init__(self, eltern, hoehe=12):
        self.rahmen = faerben(_tk.Frame(eltern, height=hoehe, highlightthickness=1),
                              bg="TROUGH", highlightbackground="BORDER",
                              highlightcolor="BORDER")
        self.rahmen.pack_propagate(False)
        self.balken = _tk.Frame(self.rahmen)
        self.rolle = "DANGER"
        self.anteil = 0.0
        self.balken.place(x=0, y=0, relwidth=self.anteil, relheight=1.0)
        self.neu_faerben()
        GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst

    def pack(self, **kw):
        self.rahmen.pack(**kw)
        return self.rahmen

    def setzen(self, anteil: float, rolle: str) -> None:
        self.anteil = max(0.0, min(1.0, anteil))
        self.rolle = rolle
        self.balken.place_configure(relwidth=self.anteil)
        self.neu_faerben()

    def neu_faerben(self) -> None:
        self.balken.configure(bg=THEMES[CURRENT_THEME][self.rolle])


# --------------------------------------------------------------------------
# Grafische Oberflaeche
# --------------------------------------------------------------------------

# So lange bleibt die grüne Bestätigung nach dem Kopieren stehen.
BESTAETIGUNG_MS = 3000


class PasswortApp:
    """Hauptfenster mit den Reitern Passwort, Erklärungen und Info."""

    def __init__(self, master) -> None:
        self.master = master
        # Das Fenster bleibt verborgen, bis es fertig aufgebaut und an seinem
        # Platz ist. Sonst zeigt Windows es beim ersten update_idletasks() an
        # der Standardposition, und es springt danach sichtbar zur Mitte.
        master.withdraw()

        einstellungen = load_config()
        self.passwort = ""
        self.aktiver_reiter = 0
        self.nachlauf = None                 # laufender after()-Auftrag zum Sichern
        self.bestaetigung_nachlauf = None    # laufender after()-Auftrag der Bestätigung
        self._status = None                  # zuletzt gezeigte Statusmeldung
        self.skalierung = max(1.0, master.winfo_fpixels("1i") / 96.0)
        self.arbeitsflaeche = self._arbeitsflaeche_ermitteln()

        master.title(f"{PROGRAMM} {VERSION}")
        master.configure(bg=BG)
        master.protocol("WM_DELETE_WINDOW", self.schliessen)

        self._variablen_anlegen(einstellungen)
        self._stil_setzen()
        self._aufbauen()
        self._fenster_einpassen()
        master.deiconify()

    # -- Bildschirm und Fenstergroesse -------------------------------------

    def _arbeitsflaeche_ermitteln(self, punkt=None) -> tuple[int, int, int, int] | None:
        """Arbeitsbereich (x, y, Breite, Höhe) eines Monitors ohne Taskleiste.

        Bei mehreren Bildschirmen umfasst winfo_screenwidth() die gesamte
        virtuelle Flaeche. Wuerde man danach zentrieren, landete das Fenster auf
        der Naht zwischen zwei Monitoren. Unter Windows liefert GetMonitorInfo
        deshalb den tatsaechlichen Arbeitsbereich.

        Ohne Punkt zaehlt der Monitor unter dem Mauszeiger - er steht dort, wo
        eben doppelgeklickt wurde. Mit Punkt (der gespeicherten Fensterlage)
        zaehlt der Monitor, auf dem dieser Punkt liegt; liegt er auf keinem -
        etwa weil ein zweiter Bildschirm abgezogen wurde -, ist die Antwort
        None und der Aufrufer zentriert stattdessen.
        """
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

                benutzer = ctypes.windll.user32
                stelle = wintypes.POINT()       # bleibt 0,0, falls die Abfrage scheitert
                if punkt is None:
                    benutzer.GetCursorPos(ctypes.byref(stelle))
                    monitor = benutzer.MonitorFromPoint(stelle, 2)   # naechstgelegener
                else:
                    stelle.x, stelle.y = int(punkt[0]), int(punkt[1])
                    monitor = benutzer.MonitorFromPoint(stelle, 0)   # keiner, wenn daneben
                if not monitor:
                    return None
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if benutzer.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    bereich = info.rcWork
                    return (bereich.left, bereich.top,
                            bereich.right - bereich.left, bereich.bottom - bereich.top)
            except (AttributeError, OSError, ValueError):
                pass
        breite, hoehe = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        if punkt is not None and not (0 <= punkt[0] < breite and 0 <= punkt[1] < hoehe):
            return None
        return (0, 0, breite, hoehe)

    def _fenster_einpassen(self) -> None:
        """Feste Fenstergröße bestimmen und das Fenster an seinen Platz legen.

        Die Groesse muss in jeder Sprache reichen, denn beim Sprachwechsel soll
        sich am Fenster nichts mehr aendern. Deshalb wird die Oberflaeche - noch
        verborgen - einmal durch alle Sprachen geschickt und der groesste Bedarf
        genommen. Die Windows-Skalierung steckt dabei schon in den gemessenen
        Werten.
        """
        breite, hoehe = self._groesster_bedarf()
        _rand_x, _rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        passt = breite <= platz_breite and hoehe <= platz_hoehe
        breite, hoehe = min(breite, platz_breite), min(hoehe, platz_hoehe)

        x, y = self._startposition(breite, hoehe)
        self.master.geometry(f"{breite}x{hoehe}+{x}+{y}")
        # Nur wenn der Inhalt ausnahmsweise nicht auf den Bildschirm passt,
        # bleibt das Fenster veraenderbar - sonst waere es nicht zu bedienen.
        self.master.resizable(not passt, not passt)
        if not passt:
            self.master.minsize(round(420 * self.skalierung), round(320 * self.skalierung))

    def _groesster_bedarf(self) -> tuple[int, int]:
        """Platzbedarf der Oberfläche über alle Sprachen hinweg."""
        start = _.language
        breite = hoehe = 0
        for code in self.sprachnamen:
            _.language = code
            texte_auffrischen()
            self._laufende_texte_auffrischen()
            self.master.update_idletasks()
            breite = max(breite, self.master.winfo_reqwidth())
            hoehe = max(hoehe, self.master.winfo_reqheight())
        _.language = start
        texte_auffrischen()
        self._laufende_texte_auffrischen()
        self.master.update_idletasks()
        return breite, hoehe

    def _startposition(self, breite: int, hoehe: int) -> tuple[int, int]:
        """Gespeicherte Lage, sonst die Bildschirmmitte.

        Beim ersten Start und bei fehlender Einstellungsdatei erscheint das
        Fenster in der Mitte des Monitors, auf dem der Mauszeiger steht. Eine
        gespeicherte Lage wird uebernommen, aber so weit hereingerueckt, dass
        das Fenster ganz auf dem Bildschirm liegt.
        """
        fenster = load_config().get("fenster")
        if isinstance(fenster, dict):
            x, y = fenster.get("x"), fenster.get("y")
            if isinstance(x, int) and isinstance(y, int):
                bereich = self._arbeitsflaeche_ermitteln((x, y))
                if bereich:
                    rand_x, rand_y, platz_breite, platz_hoehe = bereich
                    self.arbeitsflaeche = bereich
                    return (max(rand_x, min(x, rand_x + platz_breite - breite)),
                            max(rand_y, min(y, rand_y + platz_hoehe - hoehe)))
        rand_x, rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        return (rand_x + max(0, (platz_breite - breite) // 2),
                rand_y + max(0, (platz_hoehe - hoehe) // 2))

    # -- Zustand -----------------------------------------------------------

    def _variablen_anlegen(self, einstellungen: dict) -> None:
        tk = _tk
        laenge = einstellungen.get("laenge", VORGABE_LAENGE)
        if not isinstance(laenge, int) or not MIN_LAENGE <= laenge <= MAX_LAENGE:
            laenge = VORGABE_LAENGE
        self.var_laenge = tk.IntVar(value=laenge)

        gewaehlt = einstellungen.get("zeichen")
        self.var_gruppen = {}
        for gruppe in ZEICHENGRUPPEN:
            an = True
            if isinstance(gewaehlt, dict) and isinstance(gewaehlt.get(gruppe.schluessel), bool):
                an = gewaehlt[gruppe.schluessel]
            self.var_gruppen[gruppe.schluessel] = tk.BooleanVar(value=an)
        if not any(var.get() for var in self.var_gruppen.values()):
            # Alles abgewaehlt kann gespeichert worden sein, wenn die Datei von
            # Hand bearbeitet wurde - ohne Zeichen liesse sich nichts erzeugen.
            self.var_gruppen[ZEICHENGRUPPEN[1].schluessel].set(True)

        self.var_passwort = tk.StringVar(value="")
        self.var_zahl = tk.StringVar(value=str(laenge))
        self.var_status = tk.StringVar(value="")
        self.var_staerke = tk.StringVar(value="")
        self.var_vorrat = tk.StringVar(value="")
        self.var_dunkel = tk.BooleanVar(value=CURRENT_THEME == "dark")

    def _stil_setzen(self) -> None:
        """ttk-Bedienelemente an das gewählte Farbschema anpassen.

        Beim Schemawechsel genuegt es, diese Methode erneut aufzurufen: ttk
        zeichnet alle betroffenen Bedienelemente selbst neu.
        """
        tk, ttk = _tk, _ttk
        stil = ttk.Style()
        try:
            if stil.theme_use() != "clam":
                stil.theme_use("clam")
        except tk.TclError:
            pass

        for widget in ("TEntry", "TCombobox"):
            # lightcolor/darkcolor sind die 3D-Kanten des clam-Themes - ohne
            # sie zeichnet Tk im dunklen Schema weisse Raender um die Felder
            stil.configure(widget, fieldbackground=FIELD_BG, foreground=TEXT,
                           background=BTN_BG, bordercolor=BORDER,
                           lightcolor=BORDER, darkcolor=BORDER,
                           arrowcolor=TEXT, insertcolor=TEXT, padding=3)
            stil.map(widget,
                     fieldbackground=[("readonly", FIELD_BG), ("disabled", BG)],
                     background=[("readonly", BTN_BG), ("active", BTN_HOVER)],
                     foreground=[("readonly", TEXT), ("disabled", BTN_DISABLED)],
                     bordercolor=[("focus", ACCENT)],
                     lightcolor=[("focus", ACCENT)],
                     darkcolor=[("focus", ACCENT)])

        # Klappliste der Auswahlfelder ist ein klassisches Listenfeld
        self.master.option_add("*TCombobox*Listbox.background", FIELD_BG)
        self.master.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.master.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)

        stil.configure("TNotebook", background=BG, bordercolor=BORDER, borderwidth=0)
        stil.configure("TNotebook.Tab", background=TAB_BG, foreground=MUTED,
                       bordercolor=BORDER, lightcolor=TAB_BG, darkcolor=TAB_BG,
                       padding=(16, 8), font=FONT_SMALL)
        stil.map("TNotebook.Tab",
                 background=[("selected", CARD), ("active", BTN_HOVER)],
                 foreground=[("selected", TEXT)],
                 lightcolor=[("selected", CARD)],
                 darkcolor=[("selected", CARD)])

    # -- Aufbau ------------------------------------------------------------

    def _aufbauen(self) -> None:
        tk, ttk = _tk, _ttk
        GEFAERBTE_WIDGETS.clear()
        BESCHRIFTUNGEN.clear()
        self.aussen = faerben(tk.Frame(self.master), bg="BG")
        self.aussen.pack(fill="both", expand=True)

        self._kopfzeile_bauen(self.aussen)

        self.reiter = ttk.Notebook(self.aussen)
        self.reiter.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        # Alle Seiten werden gleich beim Start gebaut. Erst dadurch wechselt
        # der Reiter ohne Verzoegerung, und das Fenster kennt von Anfang an
        # seinen groessten Platzbedarf.
        for titel, bauen in ((_("Passwort"), self._seite_passwort_bauen),
                             (_("Erklärungen"), self._seite_hilfe_bauen),
                             (_("Info & Copyright"), self._seite_info_bauen)):
            seite = faerben(tk.Frame(self.reiter), bg="BG")
            self.reiter.add(seite)
            self._reiter_beschriften(seite, titel)
            bauen(seite)

        self._statusleiste_bauen(self.aussen)

        self.reiter.select(self.aktiver_reiter)
        self.reiter.bind("<<NotebookTabChanged>>",
                         lambda _e: setattr(self, "aktiver_reiter", self.reiter.index("current")))

        self.master.bind("<Control-c>", lambda _e: self.kopieren())
        self.master.bind("<F5>", lambda _e: self.erzeugen())

        # Beim Aufbau nur anzeigen, nicht speichern: Die Werte stehen ja gerade
        # erst aus der Einstellungsdatei in den Feldern.
        self._laenge_geaendert(sichern=False)
        self._auswahl_geaendert(sichern=False)
        self.status(_("Bereit – „Neu generieren“ erzeugt das Passwort."))

    def _reiter_beschriften(self, seite, titel) -> None:
        beschriftung_merken(lambda neu: self.reiter.tab(seite, text=f"  {neu}  "), titel)

    def _kopfzeile_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        kopf = faerben(tk.Frame(eltern), bg="HEADER")
        kopf.pack(fill="x")

        marke = faerben(tk.Frame(kopf), bg="HEADER")
        marke.pack(side="left", padx=18, pady=12)
        faerben(tk.Label(marke, text=PROGRAMM, font=("Segoe UI", 15, "bold"), anchor="w"),
                bg="HEADER", fg="HEADER_TITLE").pack(fill="x")
        beschriften(faerben(tk.Label(marke, font=FONT_TINY, anchor="w"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Version {version}").format(version=VERSION)).pack(fill="x")

        umschalter = faerben(tk.Frame(kopf), bg="HEADER")
        umschalter.pack(side="right", padx=18)
        beschriften(faerben(tk.Label(umschalter, font=("Segoe UI", 8, "bold"), anchor="e"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Sprache & Darstellung")).pack(fill="x", pady=(10, 2))

        zeile = faerben(tk.Frame(umschalter), bg="HEADER")
        zeile.pack(fill="x", pady=(0, 10))
        self.sprachnamen = _.available()
        self.sprachfeld = ttk.Combobox(zeile, state="readonly", font=FONT_SMALL, width=12,
                                       values=list(self.sprachnamen.values()))
        self.sprachfeld.set(self.sprachnamen[_.language])
        self.sprachfeld.pack(side="left")
        self.sprachfeld.bind("<<ComboboxSelected>>", self._sprache_gewaehlt)

        beschriften(faerben(tk.Checkbutton(zeile, variable=self.var_dunkel,
                                           command=self._schema_umgeschaltet, font=FONT_SMALL,
                                           highlightthickness=0, bd=0, cursor="hand2"),
                            bg="HEADER", fg="HEADER_TEXT", activebackground="HEADER",
                            activeforeground="HEADER_TITLE", selectcolor="HEADER_HOVER"),
                    _("Dunkel")).pack(side="left", padx=(8, 0))

    def _statusleiste_bauen(self, eltern) -> None:
        tk = _tk
        leiste = faerben(tk.Frame(eltern), bg="STATUS_BG")
        leiste.pack(side="bottom", fill="x")
        faerben(tk.Label(leiste, textvariable=self.var_status, font=FONT_SMALL, anchor="w"),
                bg="STATUS_BG", fg="MUTED").pack(side="left", padx=14, pady=4)
        faerben(tk.Label(leiste, textvariable=self.var_vorrat, font=FONT_TINY, anchor="e"),
                bg="STATUS_BG", fg="MUTED").pack(side="right", padx=(0, 14))

    # -- Reiter 1: Passwort ------------------------------------------------

    def _seite_passwort_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        # --- Erzeugtes Passwort ---
        karte = make_card(raster, fill="x")
        card_title(karte, _("Erzeugtes Passwort"))

        self.feld = faerben(
            tk.Entry(karte, textvariable=self.var_passwort, font=FONT_PASSWORT,
                     justify="center", width=MAX_LAENGE, state="readonly",
                     relief="flat", highlightthickness=1, bd=0),
            readonlybackground="FIELD_BG", fg="TEXT", disabledbackground="FIELD_BG",
            selectbackground="ACCENT", selectforeground="ON_ACCENT",
            highlightbackground="BORDER", highlightcolor="ACCENT")
        self.feld.pack(fill="x", padx=14, pady=(0, 4))

        # Dieselbe Zeile dient als ruhiger Hinweis und als grüne Bestätigung
        # nach dem Kopieren. Sie wird nicht ein- und ausgeblendet, sondern
        # wechselt nur die Farbe - so bleibt das Fenster beim Kopieren ruhig.
        # Farbe und Text richten sich nach dem Zustand; faerben() und
        # beschriften() sind dafür zu starr, das erledigt _hinweis_auffrischen().
        self.hinweis = tk.Label(karte, font=FONT_SMALL, anchor="center", pady=5)
        self.hinweis.pack(fill="x", padx=14, pady=(0, 10))
        self._hinweis_text = _("Noch kein Passwort erzeugt.")
        self._hinweis_art = "ruhe"
        self._hinweis_auffrischen()

        # --- Staerke ---
        staerke = faerben(tk.Frame(karte), bg="CARD")
        staerke.pack(fill="x", padx=14, pady=(0, 12))
        beschriften(faerben(tk.Label(staerke, font=FONT_SMALL, anchor="w"),
                            bg="CARD", fg="MUTED"), _("Stärke")).pack(side="left")
        self.staerke_text = faerben(
            tk.Label(staerke, textvariable=self.var_staerke, font=FONT_BOLD, anchor="e",
                     width=10), bg="CARD", fg="TEXT")
        self.staerke_text.pack(side="right")
        self.balken = Staerkebalken(staerke)
        self.balken.pack(side="left", fill="x", expand=True, padx=10)

        # --- Schalter ---
        knoepfe = faerben(tk.Frame(karte), bg="CARD")
        knoepfe.pack(fill="x", padx=14, pady=(0, 14))
        self.knopf_neu = FlatButton(knoepfe, _("Neu generieren"), self.erzeugen, kind="primary")
        self.knopf_neu.pack(side="left")
        self.knopf_kopieren = FlatButton(knoepfe, _("In die Zwischenablage kopieren"),
                                         self.kopieren, kind="secondary", state="disabled")
        self.knopf_kopieren.pack(side="left", padx=(10, 0))

        # --- Laenge ---
        karte_laenge = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_laenge, _("Länge"))

        zeile = faerben(tk.Frame(karte_laenge), bg="CARD")
        zeile.pack(fill="x", padx=14, pady=(0, 4))
        self.regler = faerben(
            tk.Scale(zeile, from_=MIN_LAENGE, to=MAX_LAENGE, resolution=1, orient="horizontal",
                     variable=self.var_laenge, command=lambda _w: self._laenge_geaendert(),
                     showvalue=False, sliderrelief="raised", relief="flat", bd=1,
                     highlightthickness=0, cursor="hand2", sliderlength=22, width=14),
            # Der Schieber traegt die Hintergrundfarbe des Widgets - damit er sich
            # von der Rille abhebt, ist die Rille eine Spur dunkler als die Karte.
            bg="CARD", troughcolor="BORDER", activebackground="ACCENT",
            highlightbackground="CARD")
        self.regler.pack(side="left", fill="x", expand=True)
        faerben(tk.Label(zeile, textvariable=self.var_zahl, font=FONT_ZAHL, anchor="e", width=3),
                bg="CARD", fg="TEXT").pack(side="left", padx=(12, 0))
        beschriften(faerben(tk.Label(zeile, font=FONT_SMALL, anchor="w"),
                            bg="CARD", fg="MUTED"), _("Zeichen")).pack(side="left", padx=(4, 0))

        card_text(karte_laenge,
                  _("{min} bis {max} Zeichen, in Einerschritten.").format(
                      min=MIN_LAENGE, max=MAX_LAENGE))

        # --- Zeichenauswahl ---
        karte_zeichen = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_zeichen, _("Enthaltene Zeichen"))

        gitter = faerben(tk.Frame(karte_zeichen), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        gitter.columnconfigure(1, weight=1)
        for reihe, gruppe in enumerate(ZEICHENGRUPPEN):
            haken = beschriften(faerben(
                tk.Checkbutton(gitter, variable=self.var_gruppen[gruppe.schluessel],
                               command=self._auswahl_geaendert, font=FONT_SMALL,
                               highlightthickness=0, bd=0, cursor="hand2", anchor="w"),
                bg="CARD", fg="TEXT", activebackground="CARD", activeforeground="TEXT",
                selectcolor="FIELD_BG"), _(gruppe.bezeichnung))
            haken.grid(row=reihe, column=0, sticky="w", pady=1)
            faerben(tk.Label(gitter, text=gruppe.zeichen, font=FONT_MONO_SMALL, anchor="w"),
                    bg="CARD", fg="MUTED").grid(row=reihe, column=1, sticky="w", padx=(12, 0))

    # -- Reiter 2: Erklärungen ---------------------------------------------

    def _seite_hilfe_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        karte = make_card(raster, fill="x")
        card_title(karte, _("Wie das Passwort entsteht"))
        card_text(karte, _("Gewürfelt wird mit dem Zufallsgenerator des Betriebssystems "
                           "(Python-Modul „secrets“), der für Passwörter und Schlüssel "
                           "gedacht ist. Jede angehakte Zeichengruppe kommt mindestens "
                           "einmal vor, solange die Länge dafür reicht – so scheitert ein "
                           "Passwort nicht an einer Anmeldemaske, die eine Ziffer verlangt. "
                           "Zum Schluss wird die Reihenfolge gemischt."))

        karte_staerke = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_staerke, _("Farben der Stärkeanzeige"))
        card_text(karte_staerke,
                  _("Rot: {a} bis {b} Zeichen. Gelb: {c} bis {d} Zeichen. "
                    "Grün: ab {e} Zeichen.").format(
                      a=MIN_LAENGE, b=SCHWACH_BIS, c=SCHWACH_BIS + 1, d=MITTEL_BIS,
                      e=MITTEL_BIS + 1))
        card_text(karte_staerke,
                  _("Die Anzeige richtet sich allein nach der Länge, weil sie bei einem "
                    "zufälligen Passwort am schwersten wiegt: Jedes weitere Zeichen "
                    "vervielfacht die Zahl der Möglichkeiten. Wie viele Zeichen zur "
                    "Auswahl stehen, steht rechts unten in der Fußzeile."))

        karte_daten = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_daten, _("Was gespeichert wird"))
        card_text(karte_daten,
                  _("Gespeichert werden Länge, Zeichenauswahl, Sprache, Farbschema und "
                    "Fensterlage – in der Datei {datei} neben dem Programm. Das erzeugte "
                    "Passwort selbst wird nirgends abgelegt; es verschwindet mit dem "
                    "Schließen des Fensters.").format(datei=CONFIG_NAME))

        karte_tasten = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_tasten, _("Tasten"))
        card_text(karte_tasten,
                  _("F5 erzeugt ein neues Passwort, Strg+C legt es in die Zwischenablage."))

    # -- Reiter 3: Info ----------------------------------------------------

    def _seite_info_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        karte = make_card(raster, fill="x")
        card_title(karte, f"{PROGRAMM} {VERSION}")
        card_text(karte, _("Erzeugt Passwörter aus den gewählten Zeichengruppen und legt "
                           "sie auf Wunsch in die Zwischenablage."))
        card_text(karte, "Copyright 2026 Alexander Unverhau", rolle="TEXT")
        card_text(karte, _("Erstellt mit Unterstützung von Claude AI"))
        card_text(karte, _("Veröffentlicht unter der MIT-Lizenz."))

        karte_technik = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_technik, _("Technisches"))
        gitter = faerben(tk.Frame(karte_technik), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        gitter.columnconfigure(1, weight=1)
        zeilen = (
            (_("Python"), sys.version.split()[0]),
            (_("Tkinter"), f"Tk {tk.TkVersion}"),
            (_("Zufallsquelle"), "secrets (os.urandom)"),
            (_("Einstellungen"), config_path()),
        )
        for reihe, (name, wert) in enumerate(zeilen):
            beschriften(faerben(tk.Label(gitter, font=FONT_SMALL, anchor="w"),
                                bg="CARD", fg="MUTED"), name).grid(row=reihe, column=0,
                                                                   sticky="w", pady=1)
            # wraplength deckelt die Breite: Der Ablageort der Einstellungen ist
            # ein Dateipfad, und der kann beliebig lang sein - ohne Umbruch zoege
            # er das Fenster in die Breite, je nachdem, wo das Programm liegt.
            faerben(tk.Label(gitter, text=wert, font=FONT_MONO_SMALL, anchor="w",
                             justify="left", wraplength=620),
                    bg="CARD", fg="TEXT").grid(row=reihe, column=1, sticky="w", padx=(12, 0))

    # -- Erzeugen und Kopieren ---------------------------------------------

    def gewaehlte_gruppen(self) -> list:
        return [g for g in ZEICHENGRUPPEN if self.var_gruppen[g.schluessel].get()]

    def erzeugen(self) -> None:
        """Passwort nach den gültigen Einstellungen erzeugen."""
        gruppen = self.gewaehlte_gruppen()
        if not gruppen:
            self.status(_("Bitte mindestens eine Zeichengruppe auswählen."))
            return
        laenge = self.var_laenge.get()
        self.passwort = passwort_erzeugen(laenge, gruppen)
        self.var_passwort.set(self.passwort)
        self.knopf_kopieren.configure(state="normal")
        self._hinweis_setzen(_("Fertig – zum Übernehmen kopieren."))
        self.status(_("Passwort mit {anzahl} Zeichen erzeugt.").format(anzahl=laenge))

    def kopieren(self) -> None:
        """Passwort in die Zwischenablage legen und das bestätigen."""
        if not self.passwort:
            self.status(_("Es ist noch kein Passwort vorhanden."))
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(self.passwort)
        self.master.update()                 # uebergibt den Inhalt an Windows
        self.status(_("In die Zwischenablage kopiert."))
        self._hinweis_setzen(_("In die Zwischenablage kopiert."), "erfolg")

    # -- Hinweiszeile unter dem Passwort -----------------------------------

    def _hinweis_setzen(self, text, art: str = "ruhe") -> None:
        """Zeile unter dem Passwort setzen.

        Mit art="erfolg" wird sie grün hinterlegt und blendet sich nach
        BESTAETIGUNG_MS von selbst wieder zurück.
        """
        self._hinweis_text = text
        self._hinweis_art = art
        self._hinweis_auffrischen()
        if self.bestaetigung_nachlauf is not None:
            self.master.after_cancel(self.bestaetigung_nachlauf)
            self.bestaetigung_nachlauf = None
        if art == "erfolg":
            self.bestaetigung_nachlauf = self.master.after(
                BESTAETIGUNG_MS, self._bestaetigung_zurueck)

    def _bestaetigung_zurueck(self) -> None:
        self.bestaetigung_nachlauf = None
        self._hinweis_setzen(_("Fertig – zum Übernehmen kopieren."))

    def _hinweis_auffrischen(self) -> None:
        """Text und Farben der Hinweiszeile aus dem gemerkten Zustand bilden.

        Nötig nach jedem Sprach- und Schemawechsel: Der Text steht als
        deutscher Schlüssel fest, die Farbe hängt am Zustand und nicht an
        einer festen Rolle.
        """
        text = self._hinweis_text
        if isinstance(text, Uebersetzt):
            neu = _(text.schluessel)
            text = neu.format(**text.werte) if text.werte else neu
        palette = THEMES[CURRENT_THEME]
        if self._hinweis_art == "erfolg":
            self.hinweis.configure(text=f"✓   {text}", bg=palette["OK"],
                                   fg=palette["ON_ACCENT"])
        else:
            self.hinweis.configure(text=text, bg=palette["CARD"], fg=palette["MUTED"])

    # -- Eingaben ----------------------------------------------------------

    def _laenge_geaendert(self, sichern: bool = True) -> None:
        laenge = self.var_laenge.get()
        self.var_zahl.set(str(laenge))
        stufe = staerke_stufe(laenge)
        anteil = (laenge - MIN_LAENGE) / (MAX_LAENGE - MIN_LAENGE)
        self.balken.setzen(anteil, STAERKE_ROLLE[stufe])
        self.staerke_text.configure(fg=THEMES[CURRENT_THEME][STAERKE_ROLLE[stufe]])
        self.staerke_stufe = stufe
        self.var_staerke.set(_(STAERKE_TEXT[stufe]))
        if sichern:
            self._veraltet_melden()
            self._spaeter_sichern()

    def _auswahl_geaendert(self, sichern: bool = True) -> None:
        gruppen = self.gewaehlte_gruppen()
        self.knopf_neu.configure(state="normal" if gruppen else "disabled")
        self._vorrat_zeigen()
        if not gruppen:
            self.status(_("Bitte mindestens eine Zeichengruppe auswählen."))
        else:
            self._veraltet_melden()
        if sichern:
            self._spaeter_sichern()

    def _veraltet_melden(self) -> None:
        """Nach einer Änderung daran erinnern, dass das Passwort noch das alte ist."""
        if self.passwort:
            self.status(_("Einstellung geändert – „Neu generieren“ übernimmt sie."))

    def _vorrat_zeigen(self) -> None:
        anzahl = len(vorrat_bilden(self.gewaehlte_gruppen()))
        self._vorrat = _("Zeichenvorrat: {anzahl}").format(anzahl=anzahl)
        self.var_vorrat.set(self._vorrat)

    def status(self, text) -> None:
        """Statusmeldung zeigen und für einen späteren Sprachwechsel merken."""
        self._status = text
        self.var_status.set(text)

    def _laufende_texte_auffrischen(self) -> None:
        """Texte, die zur Laufzeit entstehen, in die aktuelle Sprache bringen.

        Statusmeldung, Hinweiszeile, Staerke und Zeichenvorrat stehen nicht fest
        im Aufbau, sondern wechseln im Betrieb - texte_auffrischen() kennt sie
        deshalb nicht. Gemerkt ist jeweils der deutsche Schluessel samt
        eingesetzten Werten, sodass sie sich in jeder Sprache neu bilden lassen.
        """
        for wert, setzen in ((self._status, self.var_status.set),
                             (getattr(self, "_vorrat", None), self.var_vorrat.set)):
            if isinstance(wert, Uebersetzt):
                neu = _(wert.schluessel)
                setzen(neu.format(**wert.werte) if wert.werte else neu)
        stufe = getattr(self, "staerke_stufe", None)
        if stufe:
            self.var_staerke.set(_(STAERKE_TEXT[stufe]))
        self._hinweis_auffrischen()

    # -- Sprache und Farbschema --------------------------------------------

    def _sprache_gewaehlt(self, _ereignis=None) -> None:
        gewaehlt = self.sprachfeld.get()
        for code, name in self.sprachnamen.items():
            if name == gewaehlt:
                self.sprache_setzen(code)
                return

    def sprache_setzen(self, code: str) -> None:
        """Sprache umstellen - die Oberfläche bleibt stehen, nur die Texte wechseln.

        Das Fenster behaelt dabei Groesse und Lage: Es ist von vornherein so
        breit, dass die laengsten Beschriftungen jeder Sprache hineinpassen
        (siehe _fenster_einpassen). Waehrend die Texte getauscht werden, bleibt
        das alte Bild stehen, damit man keinen Zwischenstand sieht.
        """
        if code == _.language:
            return
        _.language = code
        einstellungen = load_config()
        einstellungen["language"] = code
        save_config(einstellungen)

        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            texte_auffrischen()
            self._laufende_texte_auffrischen()
            self.sprachfeld.set(self.sprachnamen.get(code, self.sprachfeld.get()))
            self.master.update_idletasks()
        finally:
            fortsetzen()

    def _schema_umgeschaltet(self) -> None:
        self.schema_setzen("dark" if self.var_dunkel.get() else "light")

    def schema_setzen(self, name: str) -> None:
        """Zwischen hellem und dunklem Schema wechseln - ohne Neuaufbau.

        Die Widgets bleiben stehen und werden nur umgefaerbt; ttk-Elemente
        folgen dem neu gesetzten Stil von selbst.
        """
        if name == CURRENT_THEME:
            return
        apply_theme(name)
        einstellungen = load_config()
        einstellungen["theme"] = CURRENT_THEME
        save_config(einstellungen)

        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            self.master.configure(bg=BG)
            self._stil_setzen()
            farben_auffrischen()
            # Stärkefarbe und Hinweiszeile haengen am Zustand, nicht an einer
            # festen Rolle - farben_auffrischen() kennt sie deshalb nicht.
            stufe = getattr(self, "staerke_stufe", "schwach")
            self.staerke_text.configure(fg=THEMES[CURRENT_THEME][STAERKE_ROLLE[stufe]])
            self._hinweis_auffrischen()
            self.master.update_idletasks()
        finally:
            fortsetzen()

    # -- Einstellungen sichern ---------------------------------------------

    def _spaeter_sichern(self) -> None:
        """Erst nach kurzer Ruhe speichern - der Schieberegler feuert sonst dauernd."""
        if self.nachlauf is not None:
            self.master.after_cancel(self.nachlauf)
        self.nachlauf = self.master.after(400, self._einstellungen_sichern)

    def _einstellungen_sichern(self, mit_fenster: bool = False) -> None:
        self.nachlauf = None
        einstellungen = load_config()
        einstellungen["language"] = _.language
        einstellungen["theme"] = CURRENT_THEME
        einstellungen["laenge"] = self.var_laenge.get()
        einstellungen["zeichen"] = {g.schluessel: self.var_gruppen[g.schluessel].get()
                                    for g in ZEICHENGRUPPEN}
        if mit_fenster:
            einstellungen["fenster"] = {"x": self.master.winfo_x(), "y": self.master.winfo_y()}
        save_config(einstellungen)

    def schliessen(self) -> None:
        """Einstellungen samt Fensterlage sichern und das Fenster schließen."""
        for auftrag in ("nachlauf", "bestaetigung_nachlauf"):
            if getattr(self, auftrag) is not None:
                self.master.after_cancel(getattr(self, auftrag))
                setattr(self, auftrag, None)
        self._einstellungen_sichern(mit_fenster=True)
        self.master.destroy()


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------

def dpi_bewusstsein_aktivieren() -> float:
    """Meldet die Anwendung unter Windows als DPI-bewusst an.

    Ohne diese Anmeldung vergroessert Windows das Fenster nur als Bitmap - die
    Schrift wirkt dann unscharf. Rueckgabe ist die Systemskalierung.
    """
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # System-DPI beachten
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except (AttributeError, OSError):                        # aeltere Windows-Fassungen
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError, NameError):
            pass
        return 1.0


def startfehler_melden(text: str) -> None:
    """Startfehler auf der Konsole und - wenn moeglich - in einem Fenster zeigen.

    Beim Doppelklick gibt es keine bleibende Konsole: die Meldung waere weg,
    bevor man sie lesen kann. Unter pythonw.exe ist sys.stderr sogar None, ein
    print() wuerde scheitern.
    """
    if sys.stderr is not None:
        print(text, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror(f"{PROGRAMM} {VERSION}", text)
        wurzel.destroy()
    except Exception:                       # ohne Tkinter bleibt nur die Konsole
        pass


def gui_starten() -> int:
    """Startet die Oberfläche."""
    global _tk, _ttk
    try:
        import tkinter as _tk
        from tkinter import ttk as _ttk
    except ImportError:
        startfehler_melden("Fehler: Tkinter ist nicht verfügbar. / "
                           "Error: Tkinter is not available.")
        return 2

    _.language = startup_language()
    apply_theme(startup_theme())
    widgets_bereitstellen()

    skalierung = dpi_bewusstsein_aktivieren()
    wurzel = _tk.Tk()
    if skalierung > 1.0:
        # Schriftgroessen sind in Punkt angegeben und muessen mitwachsen.
        wurzel.tk.call("tk", "scaling", skalierung * 96.0 / 72.0)
    PasswortApp(wurzel)
    wurzel.mainloop()
    return 0


def main() -> int:
    return gui_starten()


# --------------------------------------------------------------------------
# SPRACHTABELLE / LANGUAGE TABLE
#
# Quellsprache ist Deutsch - der deutsche Text im Code ist zugleich der
# Schluessel. Eine weitere Sprache kommt in drei Schritten dazu:
#   1. Kuerzel und Anzeigename in LANGUAGE_NAMES eintragen,
#      z. B.  "fr": "Francais"
#   2. In TRANSLATIONS einen Eintrag "fr": { ... } anlegen und die
#      gewuenschten Zeilen uebersetzen.
#   3. Fertig - die Auswahl oben rechts zeigt die Sprache sofort an.
#
# Nicht uebersetzte Zeilen erscheinen automatisch auf Deutsch, eine
# unvollstaendige Tabelle ist also unproblematisch. Platzhalter in
# geschweiften Klammern - {anzahl}, {min}, {datei} ... - muessen in der
# Uebersetzung unveraendert vorkommen; ihre Reihenfolge im Satz ist frei.
# --------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
}

TRANSLATIONS = {
    "en": {
        # Kopfzeile und Reiter
        "Version {version}": "Version {version}",
        "Sprache & Darstellung": "Language & appearance",
        "Dunkel": "Dark",
        "Passwort": "Password",
        "Erklärungen": "Explanations",
        "Info & Copyright": "About & copyright",

        # Reiter 1
        "Erzeugtes Passwort": "Generated password",
        "Noch kein Passwort erzeugt.": "No password generated yet.",
        "Fertig – zum Übernehmen kopieren.": "Done – copy it to use it.",
        "Stärke": "Strength",
        "Schwach": "Weak",
        "Mittel": "Medium",
        "Stark": "Strong",
        "Neu generieren": "Generate new",
        "In die Zwischenablage kopieren": "Copy to clipboard",
        "Länge": "Length",
        "Zeichen": "characters",
        "{min} bis {max} Zeichen, in Einerschritten.":
            "{min} to {max} characters, in steps of one.",
        "Enthaltene Zeichen": "Characters to include",
        "Großbuchstaben": "Uppercase letters",
        "Kleinbuchstaben": "Lowercase letters",
        "Ziffern": "Digits",
        "Satz- und Sonderzeichen": "Punctuation and special characters",

        # Statuszeile
        "Bereit – „Neu generieren“ erzeugt das Passwort.":
            "Ready – “Generate new” creates the password.",
        "Passwort mit {anzahl} Zeichen erzeugt.":
            "Generated a password of {anzahl} characters.",
        "In die Zwischenablage kopiert.": "Copied to the clipboard.",
        "Es ist noch kein Passwort vorhanden.": "There is no password yet.",
        "Bitte mindestens eine Zeichengruppe auswählen.":
            "Please select at least one group of characters.",
        "Einstellung geändert – „Neu generieren“ übernimmt sie.":
            "Setting changed – “Generate new” applies it.",
        "Zeichenvorrat: {anzahl}": "Character pool: {anzahl}",

        # Reiter 2
        "Wie das Passwort entsteht": "How the password is made",
        "Gewürfelt wird mit dem Zufallsgenerator des Betriebssystems "
        "(Python-Modul „secrets“), der für Passwörter und Schlüssel "
        "gedacht ist. Jede angehakte Zeichengruppe kommt mindestens "
        "einmal vor, solange die Länge dafür reicht – so scheitert ein "
        "Passwort nicht an einer Anmeldemaske, die eine Ziffer verlangt. "
        "Zum Schluss wird die Reihenfolge gemischt.":
            "The characters are drawn with the operating system's random "
            "generator (Python's “secrets” module), which is meant for "
            "passwords and keys. Every ticked group appears at least once as "
            "long as the length allows, so a password will not be rejected by "
            "a form that insists on a digit. Finally the order is shuffled.",
        "Farben der Stärkeanzeige": "Colours of the strength bar",
        "Rot: {a} bis {b} Zeichen. Gelb: {c} bis {d} Zeichen. "
        "Grün: ab {e} Zeichen.":
            "Red: {a} to {b} characters. Yellow: {c} to {d} characters. "
            "Green: {e} characters and up.",
        "Die Anzeige richtet sich allein nach der Länge, weil sie bei einem "
        "zufälligen Passwort am schwersten wiegt: Jedes weitere Zeichen "
        "vervielfacht die Zahl der Möglichkeiten. Wie viele Zeichen zur "
        "Auswahl stehen, steht rechts unten in der Fußzeile.":
            "The bar follows the length alone, because for a random password "
            "that is what counts most: every further character multiplies the "
            "number of possibilities. How many characters are available is "
            "shown at the bottom right.",
        "Was gespeichert wird": "What is stored",
        "Gespeichert werden Länge, Zeichenauswahl, Sprache, Farbschema und "
        "Fensterlage – in der Datei {datei} neben dem Programm. Das erzeugte "
        "Passwort selbst wird nirgends abgelegt; es verschwindet mit dem "
        "Schließen des Fensters.":
            "Length, character selection, language, colour scheme and window "
            "position are stored in the file {datei} next to the program. The "
            "generated password itself is never written down; it is gone once "
            "the window closes.",
        "Tasten": "Keys",
        "F5 erzeugt ein neues Passwort, Strg+C legt es in die Zwischenablage.":
            "F5 generates a new password, Ctrl+C puts it on the clipboard.",

        # Reiter 3
        "Erzeugt Passwörter aus den gewählten Zeichengruppen und legt "
        "sie auf Wunsch in die Zwischenablage.":
            "Generates passwords from the selected groups of characters and "
            "puts them on the clipboard on request.",
        "Erstellt mit Unterstützung von Claude AI":
            "Created with assistance of Claude AI",
        "Veröffentlicht unter der MIT-Lizenz.": "Released under the MIT licence.",
        "Technisches": "Technical details",
        "Python": "Python",
        "Tkinter": "Tkinter",
        "Zufallsquelle": "Source of randomness",
        "Einstellungen": "Settings",
    },
}


if __name__ == "__main__":
    sys.exit(main())

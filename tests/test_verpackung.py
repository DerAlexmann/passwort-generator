"""Schützt die Eigenschaften, die erst beim Packen und Veröffentlichen wichtig werden.

Diese Tests prüfen Dateien und keine Programmlogik – die Fehler, um die es geht,
zeigen sich nämlich nie beim Entwickeln: Eine EXE ohne Versionsangaben läuft
einwandfrei, ein Release ohne Prüfsumme entsteht ohne Fehlermeldung, und eine
fehlende Lizenzzeile fällt erst auf, wenn jemand danach fragt.

Jeder Test hier ist ein Wächter, und jeder wurde einmal absichtlich rot gesetzt.
Dabei hat sich gezeigt, woran solche Wächter scheitern: Ein Stichwort irgendwo
in der Datei beweist nichts. `--version-file` stand noch in einem Kommentar,
`DRITTANBIETER-LIZENZEN.md` in einer `echo`-Zeile, und „MIT" steckte im Wort
„kommt mit". Geprüft wird deshalb die Zeile, die etwas tut, und die Spalte, in
der die Angabe stehen muss.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "Passwort-Generator.pyw"
SYMBOL = WURZEL / "passwort_generator.ico"
CI = WURZEL / ".github" / "workflows" / "ci.yml"
RELEASE = WURZEL / ".github" / "workflows" / "release.yml"
DEPENDABOT = WURZEL / ".github" / "dependabot.yml"
BAUVERSIONEN = WURZEL / "requirements-build.txt"
VERSIONSINFO = WURZEL / "versionsinfo_erzeugen.py"
LIZENZHINWEISE = WURZEL / "DRITTANBIETER-LIZENZEN.md"
NOTIZ = WURZEL / "NOTICE"
IGNORIERT = WURZEL / ".gitignore"
BAUSKRIPT = WURZEL / "build.cmd"
SICHERHEIT = WURZEL / "SECURITY.md"
PROJEKTDATEI = WURZEL / "pyproject.toml"
READMES = [WURZEL / "README.md", WURZEL / "README.en.md"]

# Überschrift, an der der englische Teil der Lizenzdatei beginnt.
ENGLISCH_AB = "\n# Licenses of third-party components"

# Was in der EXE mitgeliefert wird, mit der Lizenz, die in der Lizenzspalte
# stehen muss. Die Liste stammt aus der gebauten Datei selbst: Die
# mitgelieferten .dll und .pyd lassen sich darin nachlesen. Kommt etwas hinzu,
# gehört es hierhin und in DRITTANBIETER-LIZENZEN.md – in beide Sprachteile.
BESTANDTEILE = [
    ("Python", "PSF"),
    ("Tcl/Tk", "BSD"),
    ("libtommath", "public domain"),
    ("OpenSSL", "Apache"),
    ("libffi", "MIT"),
    ("zlib-ng", "zlib"),
    ("bzip2", "BSD"),
    ("XZ Utils", "0BSD"),
    ("Zstandard", "BSD 3-Clause"),
    ("PyInstaller", "GPLv2"),
]

# Was im Quellpaket liegen muss: Lizenz und Hinweise verlangt die MIT-Lizenz,
# das Programm und sein Symbol braucht, wer es starten will.
QUELLPAKET = ["Passwort-Generator.pyw", "passwort_generator.ico", "LICENSE",
              "NOTICE", "DRITTANBIETER-LIZENZEN.md", "README.md", "README.en.md",
              "CHANGELOG.md"]

# Was neben der EXE entsteht und ans Release gehört.
ANHAENGE = ["Passwort-Generator.exe", "SHA256SUMS.txt", "DRITTANBIETER-LIZENZEN.md"]


@pytest.fixture(scope="module")
def versionsinfo():
    """versionsinfo_erzeugen.py als Modul - ein gewöhnliches Skript daneben."""
    spec = importlib.util.spec_from_file_location("versionsinfo_erzeugen", VERSIONSINFO)
    assert spec is not None and spec.loader is not None, (
        f"Konnte für {VERSIONSINFO} keine Modulspezifikation erzeugen.")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def pyinstaller_versioninfo():
    """PyInstallers Leser für Versionsdateien - in der CI Pflicht."""
    if os.environ.get("PYINSTALLER_PFLICHT") not in (None, "", "0"):
        # In der CI ist er Pflicht: Ein Überspringen wäre grün, ohne dass die
        # festgenagelte Fassung von PyInstaller etwas geprüft hätte.
        from PyInstaller.utils.win32 import versioninfo
        return versioninfo
    return pytest.importorskip(
        "PyInstaller.utils.win32.versioninfo",
        reason="PyInstaller wird nur zum Bauen gebraucht, nicht für die Tests")


# --- Hilfsmittel -----------------------------------------------------------

def _ohne_kommentare(datei: Path) -> str:
    """Dateitext ohne Kommentarzeilen, Fortsetzungszeilen zusammengefügt.

    Ein Kommentar beweist nichts: „# fail_on_unmatched_files: true" würde jede
    Prüfung bestehen, ohne dass die Einstellung gesetzt wäre.
    """
    text = re.sub(r"(?m)^\s*#.*$", "", datei.read_text(encoding="utf-8"))
    return text.replace("\\\n", " ")


def _jobbloecke(datei: Path) -> dict[str, str]:
    """Einen Workflow in seine Jobs zerlegen: Name -> Textblock.

    Absichtlich ohne YAML-Leser: Die Testumgebung soll außer pytest nichts
    brauchen. Gelesen wird erst ab „jobs:", sonst gerieten „push" und
    „workflow_dispatch" unter „on:" mit in die Liste - sie sind genauso
    eingerückt, sind aber keine Jobs.
    """
    text = _ohne_kommentare(datei)
    _, stichwort, jobs = text.partition("\njobs:\n")
    assert stichwort, f"In {datei.name} fehlt der Abschnitt jobs:."
    stellen = [(treffer.group(1), treffer.start())
               for treffer in re.finditer(r"^  ([\w-]+):$", jobs, re.MULTILINE)]
    assert stellen, f"In {datei.name} ließ sich kein Job finden."
    bloecke = {}
    for nummer, (name, anfang) in enumerate(stellen):
        ende = stellen[nummer + 1][1] if nummer + 1 < len(stellen) else len(jobs)
        bloecke[name] = jobs[anfang:ende]
    return bloecke


def _job(datei: Path, name: str) -> str:
    """Ein Jobblock, mit Klartext statt KeyError, wenn er umbenannt wurde."""
    bloecke = _jobbloecke(datei)
    assert name in bloecke, (
        f"In {datei.name} gibt es keinen Job {name!r} mehr (vorhanden: "
        f"{sorted(bloecke)}) - wurde er umbenannt, prüft dieser Test nichts.")
    return bloecke[name]


def _blockliste(text: str, schluessel: str) -> list[str]:
    """Die Zeilen eines mehrzeiligen YAML-Blocks nach „schluessel: |".

    Damit lässt sich prüfen, welche Dateien wirklich hochgeladen und ans
    Release gehängt werden - und nicht nur, ob ein Name irgendwo vorkommt.
    """
    treffer = re.search(rf"^(\s*){re.escape(schluessel)}:\s*\|\s*$", text, re.MULTILINE)
    assert treffer, f"Kein mehrzeiliger Block {schluessel!r} gefunden."
    tiefe = len(treffer.group(1))
    eintraege = []
    for zeile in text[treffer.end():].splitlines()[1:]:
        if not zeile.strip():
            continue
        if len(zeile) - len(zeile.lstrip()) <= tiefe:
            break
        eintraege.append(zeile.strip())
    assert eintraege, f"Der Block {schluessel!r} ist leer."
    return eintraege


def _sprachteile() -> list[tuple[str, str]]:
    """Die Lizenzdatei in ihren deutschen und ihren englischen Teil zerlegen.

    Ohne diese Trennung zählt „zweimal dieselbe Zeile" als „in beiden
    Sprachen" - eine gelöschte englische Tabellenzeile fiele nicht auf.
    """
    text = LIZENZHINWEISE.read_text(encoding="utf-8")
    deutsch, trenner, englisch = text.partition(ENGLISCH_AB)
    assert trenner, (
        f"In {LIZENZHINWEISE.name} fehlt die Überschrift des englischen Teils "
        f"({ENGLISCH_AB.strip()!r}).")
    return [("deutsch", deutsch), ("englisch", englisch)]


def _tabellenzeilen(text: str, name: str) -> list[str]:
    """Zeilen der Lizenztabelle, deren fett gesetzter Name passt."""
    gesucht = re.escape(name.replace("_", "-"))
    return re.findall(rf"^\|\s*\*\*{gesucht}\*\*.*$", text, re.MULTILINE | re.IGNORECASE)


def _lizenzspalte(zeile: str) -> str:
    """Die mittlere Spalte einer Tabellenzeile - dort steht die Lizenz.

    Die ganze Zeile zu durchsuchen wäre blind: „MIT" steckt in „kommt mit
    `ctypes`", und „zlib" im Namen „zlib-ng" und in jeder URL dorthin.
    """
    spalten = [teil.strip() for teil in zeile.strip().strip("|").split("|")]
    assert len(spalten) == 3, f"Keine dreispaltige Tabellenzeile: {zeile!r}"
    return spalten[1]


def _vier_stellen(ffi) -> tuple[int, int, int, int]:
    """Die vier Stellen der Version aus den Wortpaaren, die Windows speichert.

    Gelesen wird, was wirklich in der Ressource steht: PyInstaller legt die
    Zahlen als je zwei 16-Bit-Hälften ab.
    """
    return (ffi.fileVersionMS >> 16, ffi.fileVersionMS & 0xFFFF,
            ffi.fileVersionLS >> 16, ffi.fileVersionLS & 0xFFFF)


def _bau_python() -> str:
    """Die Python-Fassung, mit der die EXE gepackt wird - aus requirements-build.txt."""
    treffer = re.findall(r"^#\s*Python:\s*(\d+\.\d+)\s*$",
                         BAUVERSIONEN.read_text(encoding="utf-8"), re.MULTILINE)
    assert len(treffer) == 1, (
        f"{BAUVERSIONEN.name} muss genau eine Zeile '# Python: X.Y' enthalten "
        f"(gefunden: {len(treffer)}) - sonst weiß niemand, welche Laufzeit in "
        "der EXE steckt.")
    return treffer[0]


def _versionen(datei: Path) -> dict[str, tuple[str, tuple[int, ...]]]:
    """Paketname -> (Vergleich, Versionszahlen) aus einer requirements-Datei."""
    paare = {}
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.split("#")[0].strip()
        if not zeile:
            continue
        treffer = re.fullmatch(r"([\w.\-]+)\s*(==|>=)\s*(\d+(?:\.\d+)*)", zeile)
        assert treffer, (
            f"{datei.name}: {zeile!r} ist weder ==X.Y noch >=X.Y - diese "
            "Prüfung versteht nur einfache Zeilen.")
        name, vergleich, version = treffer.groups()
        paare[name.lower()] = (vergleich, tuple(int(teil) for teil in version.split(".")))
    return paare


def _bauskript() -> str:
    """build.cmd ohne REM-Zeilen, Fortsetzungen zusammengefügt.

    Erklärende Kommentare und `echo`-Zeilen nennen dieselben Namen wie die
    Befehle. Geprüft werden soll aber der Befehl.
    """
    zeilen = [zeile for zeile in BAUSKRIPT.read_text(encoding="utf-8").splitlines()
              if not zeile.lstrip().upper().startswith("REM")]
    return "\n".join(zeilen).replace(" ^\n", " ")


# --- Versionsangaben in der EXE -------------------------------------------

def test_versionsangaben_kommen_aus_dem_quelltext(pg, versionsinfo):
    # Eine zweite Stelle mit der Versionsnummer wäre eine Stelle zu viel: Der
    # Erzeuger liest PROGRAMM und VERSION aus der .pyw - aus derselben Quelle
    # wie Kopfzeile und Infoseite. Zwei unabhängige Leseweisen (Suchausdruck
    # gegen Import) müssen dasselbe ergeben.
    assert versionsinfo._aus_quelltext("VERSION") == pg.VERSION
    assert versionsinfo._aus_quelltext("PROGRAMM") == pg.PROGRAMM


def test_inhalt_nutzt_seine_argumente(versionsinfo, pyinstaller_versioninfo, tmp_path):
    # Mit Namen, die nirgends im Projekt vorkommen: Prüfte der Test mit der
    # eigenen Version, bliebe eine fest eingebaute Nummer in inhalt()
    # unbemerkt - sie stimmte ja zufällig.
    text = versionsinfo.inhalt("Foo-Bar", "9.8.7")
    datei = tmp_path / "versionsinfo.txt"
    datei.write_text(text, encoding="utf-8")

    info = pyinstaller_versioninfo.load_version_info_from_text_file(str(datei))
    felder = {eintrag.name: eintrag.val for eintrag in info.kids[0].kids[0].kids}
    assert felder["ProductName"] == "Foo-Bar"
    assert felder["ProductVersion"] == "9.8.7"
    # Der Explorer zeigt zwei Versionen an: Produkt- und Dateiversion. Beide
    # müssen dieselbe Nummer nennen, sonst sucht man den Unterschied.
    assert felder["FileVersion"] == "9.8.7"
    assert felder["InternalName"] == "Foo-Bar"
    assert felder["OriginalFilename"] == "Foo-Bar.exe"
    assert _vier_stellen(info.ffi) == (9, 8, 7, 0)
    # Datei- und Produktversion müssen dieselben Zahlen tragen.
    assert info.ffi.productVersionMS == info.ffi.fileVersionMS
    assert info.ffi.productVersionLS == info.ffi.fileVersionLS
    # Urheber, Lizenz und der Hinweis auf die KI-Mithilfe stehen überall dort,
    # wo auch der Copyright-Vermerk steht - die Dateieigenschaften sind so
    # eine Stelle. Dazu der Zeiger auf die Lizenzen der Fremdkomponenten.
    # Gegen pyproject.toml und nicht gegen die eigene Konstante: Sonst prüfte
    # der Test nur, dass das Skript sich selbst gleicht.
    urheber = re.search(r'authors\s*=\s*\[\{\s*name\s*=\s*"([^"]+)"',
                        PROJEKTDATEI.read_text(encoding="utf-8"))
    assert urheber, "pyproject.toml nennt keinen Urheber."
    assert felder["CompanyName"] == urheber[1]
    assert "MIT" in felder["LegalCopyright"]
    assert "Claude AI" in felder["LegalCopyright"]
    assert LIZENZHINWEISE.name in felder["Comments"]


def test_erzeugte_datei_passt_zum_programm(versionsinfo, pyinstaller_versioninfo,
                                           tmp_path, pg):
    # Und derselbe Weg mit den echten Angaben: Was im Release entsteht, muss
    # Produktname und Version des Programms tragen.
    datei = tmp_path / "versionsinfo.txt"
    datei.write_text(versionsinfo.inhalt(pg.PROGRAMM, pg.VERSION), encoding="utf-8")
    info = pyinstaller_versioninfo.load_version_info_from_text_file(str(datei))
    felder = {eintrag.name: eintrag.val for eintrag in info.kids[0].kids[0].kids}
    assert felder["ProductName"] == pg.PROGRAMM
    assert felder["ProductVersion"] == pg.VERSION
    assert felder["OriginalFilename"] == f"{pg.PROGRAMM}.exe"


def test_main_schreibt_die_datei_aus_der_quelle(versionsinfo, tmp_path, monkeypatch):
    # main() ruft kein Test auf, wenn man es nicht ausdrücklich tut - und im
    # Release ist genau dieser Aufruf der Schritt vor dem Packen.
    quelle = tmp_path / "Probe.pyw"
    quelle.write_text('PROGRAMM = "Probe-Programm"\nVERSION = "9.8.7"\n', encoding="utf-8")
    ziel = tmp_path / "versionsinfo.txt"
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)
    monkeypatch.setattr(versionsinfo, "ZIEL", ziel)

    versionsinfo.main()

    roh = ziel.read_bytes()
    assert b"\r\n" not in roh, "Die Versionsdatei soll mit LF geschrieben werden."
    text = roh.decode("utf-8")
    assert "StringStruct('ProductName', 'Probe-Programm')" in text
    assert "StringStruct('ProductVersion', '9.8.7')" in text
    assert "filevers=(9, 8, 7, 0)" in text


def test_ziel_heisst_wie_ueberall_sonst(versionsinfo):
    # Der Dateiname steht in build.cmd, im Release-Workflow und in .gitignore.
    # Hieße die erzeugte Datei anders, packte PyInstaller eine alte mit ein
    # oder bräche ab - und sie läge plötzlich im Repository.
    assert versionsinfo.ZIEL.name == "versionsinfo.txt"
    assert "versionsinfo.txt" in _bauskript()
    assert "versionsinfo.txt" in _ohne_kommentare(RELEASE)


@pytest.mark.parametrize(
    ("fall", "quelltext", "stichwort"),
    [
        ("fehlt", 'ANDERES = "x"\n', "0-mal"),
        ("doppelt", 'VERSION = "1.0"\nVERSION = "2.0"\n', "2-mal"),
        ("Umlaut", 'VERSION = "1.0ä"\n', "ASCII"),
    ],
)
def test_quelltext_ohne_eindeutige_angabe_bricht_ab(versionsinfo, tmp_path, monkeypatch,
                                                    fall, quelltext, stichwort):
    # Lieber laut abbrechen als raten: Stünde VERSION zweimal am Zeilenanfang,
    # nähme der Suchausdruck den ersten und Python den letzten Wert. Ein
    # Umlaut wiederum landete als kaputtes Zeichen in den Dateieigenschaften.
    quelle = tmp_path / "Probe.pyw"
    quelle.write_text(quelltext, encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)
    with pytest.raises(SystemExit) as fehler:
        versionsinfo._aus_quelltext("VERSION")
    assert stichwort in str(fehler.value), f"Fall {fall}: Meldung nennt den Grund nicht."


@pytest.mark.parametrize(
    ("version", "erwartet"),
    [
        ("1.3.1", (1, 3, 1, 0)),
        ("2.10.3", (2, 10, 3, 0)),
        ("1.2", (1, 2, 0, 0)),
        ("1", (1, 0, 0, 0)),
        ("1.3.1.4", (1, 3, 1, 4)),
        ("1.65535.0", (1, 65535, 0, 0)),        # genau an der Grenze
    ],
)
def test_vierstellig_rechnet_richtig(versionsinfo, version, erwartet):
    # Von Hand hingeschrieben und nicht mit derselben Funktion errechnet: Sonst
    # prüfte der Test nur, dass die Funktion sich selbst gleicht.
    assert versionsinfo.vierstellig(version) == erwartet


@pytest.mark.parametrize(
    ("version", "stichwort"),
    [
        ("1.3.1rc1", "Ziffern und Punkte"),
        ("1.3.1-beta", "Ziffern und Punkte"),
        ("v1.3.1", "Ziffern und Punkte"),
        ("", "Ziffern und Punkte"),
        ("1..0", "Ziffern und Punkte"),
        ("1.-2.0", "Ziffern und Punkte"),
        ("-1", "Ziffern und Punkte"),
        ("1_0.2", "Ziffern und Punkte"),         # int() nähme das an
        (" 1.2", "Ziffern und Punkte"),          # int() auch das
        ("+1.2", "Ziffern und Punkte"),          # und das
        ("1.2.3.4.5", "vier Stellen"),
        ("1.70000.0", "zwischen 0 und"),
        ("1.65536.0", "zwischen 0 und"),         # eine Stelle über der Grenze
    ],
)
def test_vierstellig_lehnt_unbrauchbares_mit_klartext_ab(versionsinfo, version, stichwort):
    # Ein „invalid literal for int()" mitten im Release-Lauf sagt niemandem,
    # dass VERSION gemeint ist. Jeder Zweig nennt außerdem einen anderen
    # Grund - sonst prüfte der Test nur, dass überhaupt etwas schiefging.
    with pytest.raises(SystemExit) as fehler:
        versionsinfo.vierstellig(version)
    meldung = str(fehler.value)
    assert "VERSION" in meldung
    assert stichwort in meldung, f"{version!r}: erwartet war der Grund {stichwort!r}."


def test_versionsdatei_gehoert_nicht_ins_repository():
    # Sie ist abgeleitet und wird vor jedem Packen neu erzeugt. Im Repository
    # wäre sie eine zweite Stelle mit der Versionsnummer, die veraltet.
    assert re.search(r"^versionsinfo\.txt$", IGNORIERT.read_text(encoding="utf-8"),
                     re.MULTILINE), "versionsinfo.txt fehlt in .gitignore."
    # Und Git muss es auch so sehen: Ein späteres „!versionsinfo.txt" oder eine
    # bereits verfolgte Datei höbe die Zeile wieder auf.
    try:
        ergebnis = subprocess.run(["git", "check-ignore", "-q", "versionsinfo.txt"],
                                  cwd=WURZEL, capture_output=True)
    except (OSError, subprocess.SubprocessError):       # kein Git zur Hand
        pytest.skip("git ist hier nicht aufrufbar")
    assert ergebnis.returncode == 0, (
        "git sieht versionsinfo.txt nicht als ignoriert an.")


def test_version_steht_nur_in_der_programmdatei(pg):
    # pyproject.toml nennt die Version ein zweites Mal. Der Tag-Vergleich im
    # Release sieht nur die EXE, also nur die .pyw - eine vergessene Anhebung
    # hier fiele sonst nirgends auf.
    treffer = re.findall(r'^version\s*=\s*"([^"]+)"', PROJEKTDATEI.read_text(encoding="utf-8"),
                         re.MULTILINE)
    assert treffer == [pg.VERSION], (
        f"pyproject.toml nennt {treffer} statt {[pg.VERSION]} - die beiden "
        "Stellen sind auseinandergelaufen.")


def test_bauskript_baut_wie_der_release():
    # Der Bau auf dem eigenen Rechner soll dasselbe ergeben wie der im
    # Release: dieselben Versionsangaben, dasselbe Symbol, dieselben
    # Lizenzhinweise neben der Datei.
    text = _bauskript()
    assert re.search(r"^\s*%PY%\s+versionsinfo_erzeugen\.py\s*$", text, re.MULTILINE), (
        "build.cmd erzeugt die Versionsangaben nicht - die EXE bliebe ohne.")

    aufruf = re.search(r"^\s*%PY% -m PyInstaller .*$", text, re.MULTILINE)
    assert aufruf, "In build.cmd steht kein PyInstaller-Aufruf mehr."
    assert '--version-file "versionsinfo.txt"' in aufruf.group(0), (
        "Der PyInstaller-Aufruf bekommt die Versionsdatei nicht übergeben.")
    assert f'--icon "{SYMBOL.name}"' in aufruf.group(0), (
        "Der PyInstaller-Aufruf baut ohne Programmsymbol.")

    # Die copy-Zeile, nicht die echo-Zeile daneben: Genau daran ist dieser
    # Wächter beim Rotsetzen einmal grün geblieben.
    assert re.search(rf'^\s*copy\s+/y\s+"{re.escape(LIZENZHINWEISE.name)}"\s+"dist',
                     text, re.MULTILINE | re.IGNORECASE), (
        "build.cmd legt die Lizenzhinweise nicht neben die EXE.")

    # Jeder der drei Schritte muss bei einem Fehler abbrechen - sonst meldet
    # das Skript „Fertig" über Dateien, die es nicht gibt.
    assert len(re.findall(r"^if errorlevel 1 \($", text, re.MULTILINE)) >= 3, (
        "Nach einem der Schritte in build.cmd fehlt die Fehlerprüfung.")


def test_programmsymbol_liegt_im_projekt():
    # Ohne die .ico bricht der Bau mit einer Meldung über eine fehlende Datei
    # ab. Eine leere oder vertauschte Datei nähme PyInstaller dagegen an.
    assert SYMBOL.is_file(), (
        f"{SYMBOL.name} fehlt - neu erzeugen mit: python icon_erzeugen.py")
    roh = SYMBOL.read_bytes()
    assert len(roh) > 1000, f"{SYMBOL.name} ist verdächtig klein ({len(roh)} Bytes)."
    assert roh[:4] == b"\x00\x00\x01\x00", f"{SYMBOL.name} ist keine .ico-Datei."


# --- Fester Bau ------------------------------------------------------------

def test_bauversionen_sind_festgenagelt():
    # Untergrenzen sind für die Tests richtig, für die veröffentlichte EXE
    # nicht: Die ausgelieferte Datei hinge sonst davon ab, was am Tag des Baus
    # die neueste Fassung war. Der Suchausdruck in _versionen() lässt auch
    # Platzhalter wie „==6.*" nicht durch.
    fest = _versionen(BAUVERSIONEN)
    assert fest, f"{BAUVERSIONEN.name} nennt kein einziges Paket"
    assert "pyinstaller" in fest, (
        f"{BAUVERSIONEN.name} nennt PyInstaller nicht - womit wird gepackt?")
    for name, (vergleich, _version) in fest.items():
        assert vergleich == "==", (
            f"{name} ist in {BAUVERSIONEN.name} nicht festgenagelt.")


def test_python_fassung_steht_ueberall_gleich():
    # Die Laufzeit in der EXE ist der größte Fremdanteil darin. Steht sie an
    # fünf Stellen und driftet auseinander, prüft die CI eine andere Fassung,
    # als ausgeliefert wird, und die Lizenzdatei nennt eine falsche.
    fassung = _bau_python()

    treffer = re.search(r'python-version:\s*"([\d.]+)"', _job(RELEASE, "windows-exe"))
    assert treffer, "Der EXE-Job legt keine Python-Fassung fest."
    assert treffer[1] == fassung, (
        f"Der Release baut mit Python {treffer[1]}, {BAUVERSIONEN.name} nennt {fassung}.")

    treffer = re.search(r'python-version:\s*"([\d.]+)"', _job(CI, "bauversionen"))
    assert treffer, "Der CI-Job für den festen Bau legt keine Python-Fassung fest."
    assert treffer[1] == fassung, (
        f"Die CI baut mit Python {treffer[1]}, ausgeliefert wird {fassung}.")

    matrix = re.search(r"python:\s*\[([^\]]*)\]", _job(CI, "tests"))
    assert matrix, "Die CI hat keine Python-Matrix mehr?"
    assert f'"{fassung}"' in matrix[1], (
        f"Python {fassung} wandert in die EXE, wird in der CI aber nicht "
        f"getestet (Matrix: {matrix[1].strip()}).")

    for sprache, teil in _sprachteile():
        zeile = _tabellenzeilen(teil, "Python")
        assert len(zeile) == 1, f"{sprache}: keine eindeutige Zeile zu Python."
        assert re.search(rf"\*\*Python\*\*\s*{re.escape(fassung)}\b", zeile[0]), (
            f"{sprache}: Die Lizenzdatei nennt nicht Python {fassung}.")


def test_ci_prueft_die_festgenagelten_versionen():
    # Ohne diesen Job liefe die gepinnte Fassung von PyInstaller erstmals beim
    # Tag - und ein Fehler dort kippte den Release.
    block = _job(CI, "bauversionen")
    assert f"-r {BAUVERSIONEN.name}" in block, (
        f"Der CI-Job installiert {BAUVERSIONEN.name} nicht.")
    assert re.search(r"^\s*run:\s*python versionsinfo_erzeugen\.py\s*$", block, re.MULTILINE), (
        "Der Job installiert die festen Versionen, benutzt sie aber nicht.")
    assert re.search(r'^\s*PYINSTALLER_PFLICHT:\s*"1"\s*$', block, re.MULTILINE), (
        "Ohne PYINSTALLER_PFLICHT: \"1\" darf sich der Test überspringen - und "
        "ein Überspringen ist grün, ohne dass etwas geprüft wurde.")
    assert Path(__file__).name in block, (
        f"Der Job ruft {Path(__file__).name} nicht auf.")


def _dependabot_bloecke() -> dict[str, str]:
    """Die Einträge unter updates: nach ihrem package-ecosystem."""
    text = _ohne_kommentare(DEPENDABOT)
    _, stichwort, rest = text.partition("\nupdates:\n")
    assert stichwort, "In dependabot.yml fehlt der Abschnitt updates:."
    stellen = [treffer.start() for treffer in re.finditer(r"^  - ", rest, re.MULTILINE)]
    assert stellen, "In dependabot.yml steht kein einziger Eintrag."
    bloecke = {}
    for nummer, anfang in enumerate(stellen):
        ende = stellen[nummer + 1] if nummer + 1 < len(stellen) else len(rest)
        block = rest[anfang:ende]
        name = re.search(r'package-ecosystem:\s*"?([\w-]+)"?', block)
        assert name, f"Ein Eintrag nennt kein package-ecosystem:\n{block}"
        bloecke[name[1]] = block
    return bloecke


def test_dependabot_laesst_die_untergrenzen_in_ruhe():
    # Ohne diese Einstellung hebt Dependabot auch Untergrenzen an. Die
    # Untergrenze nennt aber die älteste Fassung, mit der etwas läuft; eine
    # Anhebung verwehrt allen dazwischen die Installation, ohne Nutzen.
    # Angehoben werden soll nur, was fest ist.
    bloecke = _dependabot_bloecke()
    assert "pip" in bloecke, (
        f"Dependabot pflegt kein pip mehr (nur {sorted(bloecke)}) - die festen "
        "Bauversionen bliebe dann niemand im Blick.")
    assert re.search(r'^\s*versioning-strategy:\s*"?increase-if-necessary"?\s*$',
                     bloecke["pip"], re.MULTILINE), (
        "Dem pip-Eintrag fehlt versioning-strategy: increase-if-necessary.")
    assert "github-actions" in bloecke, (
        "Dependabot pflegt die Actions in den Workflows nicht - niemand sonst "
        "tut es.")
    for name, block in bloecke.items():
        assert re.search(r'^\s*directory:\s*"/"\s*$', block, re.MULTILINE), (
            f"Der Eintrag {name} sieht nicht im Projektstamm nach.")


# --- Lizenzen der Fremdkomponenten ----------------------------------------

@pytest.mark.parametrize(("name", "lizenz"), BESTANDTEILE,
                         ids=[name for name, _ in BESTANDTEILE])
def test_lizenzhinweise_nennen_jeden_bestandteil(name, lizenz):
    # Was in der EXE liegt, muss mit Lizenz und Quelle genannt sein - in
    # beiden Sprachteilen, und die Lizenz in ihrer Spalte.
    for sprache, teil in _sprachteile():
        zeilen = _tabellenzeilen(teil, name)
        assert len(zeilen) == 1, (
            f"{sprache}: {name} braucht in {LIZENZHINWEISE.name} genau eine "
            f"Tabellenzeile (gefunden: {len(zeilen)}).")
        spalte = _lizenzspalte(zeilen[0])
        assert re.search(rf"\b{re.escape(lizenz)}\b", spalte), (
            f"{sprache}: Die Lizenzspalte zu {name} lautet {spalte!r} und "
            f"nennt {lizenz!r} nicht.")
        assert "http" in zeilen[0], (
            f"{sprache}: Die Zeile zu {name} verweist auf keinen Lizenztext.")


def test_lizenzhinweise_nennen_die_ausnahme_von_pyinstaller():
    # Der Bootloader ist der einzige Teil unter Copyleft. Ohne die Ausnahme in
    # seiner Lizenz stünde die ganze EXE unter der GPL - diese Ausnahme ist
    # also der Grund, warum sie MIT bleiben darf, und gehört genannt.
    for sprache, teil in _sprachteile():
        wort = "Ausnahme" if sprache == "deutsch" else "exception"
        zeilen = _tabellenzeilen(teil, "PyInstaller")
        assert len(zeilen) == 1, f"{sprache}: keine eindeutige PyInstaller-Zeile."
        assert wort in zeilen[0], (
            f"{sprache}: Die PyInstaller-Zeile nennt {wort!r} nicht.")


@pytest.mark.parametrize("paket", sorted(_versionen(BAUVERSIONEN)))
def test_lizenzhinweise_nennen_jede_bauabhaengigkeit(paket):
    # Was beim Packen mitkommt, landet in der EXE - der Bootloader von
    # PyInstaller steckt in jeder gebauten Datei.
    for sprache, teil in _sprachteile():
        assert len(_tabellenzeilen(teil, paket)) == 1, (
            f"{sprache}: {paket} steht in {BAUVERSIONEN.name}, hat in "
            f"{LIZENZHINWEISE.name} aber keine Tabellenzeile.")


def test_lizenzhinweise_liegen_dem_release_bei():
    # Im Repository zu stehen genügt nicht: Wer nur die EXE herunterlädt, muss
    # die Lizenzen trotzdem bekommen.
    yaml = _ohne_kommentare(RELEASE)
    assert re.search(rf"^\s*cp .*{re.escape(LIZENZHINWEISE.name)}", yaml, re.MULTILINE), (
        "Die Hinweise fehlen im Quellpaket.")
    assert re.search(rf"^\s*run: Copy-Item {re.escape(LIZENZHINWEISE.name)} dist/\s*$",
                     yaml, re.MULTILINE), (
        "Die Hinweise werden nicht neben die EXE gelegt.")


@pytest.mark.parametrize("datei", QUELLPAKET)
def test_quellpaket_enthaelt_lizenz_und_programm(datei):
    # LICENSE und NOTICE verlangt die MIT-Lizenz, das Programm und sein Symbol
    # braucht, wer das Skript statt der EXE nimmt.
    zeile = re.search(r"^\s*cp .*out/Passwort-Generator/\s*$",
                      _ohne_kommentare(RELEASE), re.MULTILINE)
    assert zeile, "Im Quellpaket-Job wird nichts mehr kopiert."
    assert re.search(rf"(^|\s){re.escape(datei)}(\s|$)", zeile.group(0)), (
        f"{datei} fehlt im Quellpaket.")


def test_readmes_und_notiz_verweisen_auf_die_lizenzhinweise():
    # Dort sucht ein Anwender nach Lizenzen - nicht in einer Datei, von deren
    # Namen er nichts weiß.
    for readme in READMES:
        assert LIZENZHINWEISE.name in readme.read_text(encoding="utf-8"), (
            f"{readme.name} verweist nicht auf {LIZENZHINWEISE.name}.")
    # NOTICE sagt es zweimal, deutsch und englisch - wie alles in dieser
    # Datei. Eine der beiden Stellen zu streichen genügt, damit ein Leser die
    # Lizenzdatei nicht findet.
    assert NOTIZ.read_text(encoding="utf-8").count(LIZENZHINWEISE.name) >= 2, (
        f"NOTICE verweist nicht in beiden Sprachen auf {LIZENZHINWEISE.name}.")


# --- Release-Workflow ------------------------------------------------------

def test_release_erzeugt_und_uebergibt_die_versionsdatei():
    # Ohne --version-file bleiben die Dateieigenschaften leer, und die EXE
    # verriete nicht einmal ihre eigene Fassung.
    block = _job(RELEASE, "windows-exe")
    assert re.search(r"^\s*run: python versionsinfo_erzeugen\.py\s*$", block, re.MULTILINE), (
        "Die Versionsdatei wird im Release nicht erzeugt.")
    assert "--version-file versionsinfo.txt" in block, (
        "PyInstaller bekommt die Versionsdatei nicht übergeben.")
    assert f"--icon {SYMBOL.name}" in block, "Die EXE wird ohne Symbol gebaut."


def test_release_haelt_den_tag_gegen_die_version():
    # Das ist die einzige Sicherung gegen eine vergessene Anhebung von
    # VERSION. Geprüft wird der Vergleich selbst: Ein gedrehtes -eq oder ein
    # throw, das zu Write-Output wird, ließe den Release mit der falschen
    # Nummer durchlaufen und fiele erst dem Anwender auf.
    block = _job(RELEASE, "windows-exe")
    assert re.search(
        r"if \(-not \$info\.ProductName -or -not \$info\.ProductVersion\) \{\s*\n\s*throw ",
        block), (
        "Eine leere Versionsressource wird nicht mit throw abgelehnt.")
    assert re.search(
        r"if \(\$env:GITHUB_REF_TYPE -eq 'tag' -and "
        r'"v\$\(\$info\.ProductVersion\)" -ne \$env:GITHUB_REF_NAME\) \{\s*\n\s*throw ',
        block), (
        "Der Tag wird nicht mit throw gegen die Version der EXE gehalten - "
        "erwartet war genau: Bei einem Tag muss v<ProductVersion> der "
        "Tag-Name sein.")


def test_release_prueft_ob_die_exe_wirklich_startet():
    # Dass der Prozess noch lebt, beweist nichts: Faellt das Programm beim
    # Start um, zeigt es ein Meldungsfenster und wartet darin. Erst die
    # Einstellungsdatei belegt, dass die Oberfläche fertig aufgebaut war.
    block = _job(RELEASE, "windows-exe")
    assert "Start-Process" in block, "Die EXE wird nicht einmal gestartet."
    assert "MainWindowHandle" in block, "Es wird nicht geprüft, ob ein Fenster da ist."
    assert "CloseMainWindow" in block, "Das Fenster wird nicht wie von Hand geschlossen."
    assert re.search(r"if \(-not \(Test-Path \$einstellungen\)\) \{\s*\n\s*throw ", block), (
        "Ob beim Schließen Einstellungen entstehen, wird nicht mit throw "
        "geprüft - ein Meldungsfenster käme sonst als „läuft“ durch.")
    assert re.search(r"if \(\$p\.HasExited\) \{ throw ", block), (
        "Ein sofortiger Absturz wird nicht als Fehler gemeldet.")


def test_release_bildet_die_pruefsumme_und_liest_sie_zurueck():
    # Die EXE ist nicht signiert. Die Prüfsumme ist das Einzige, womit ein
    # Anwender die heruntergeladene Datei vergleichen kann - sie muss stimmen
    # und lesbar sein.
    block = _job(RELEASE, "windows-exe")
    assert re.search(r"Get-FileHash .*-Algorithm SHA256", block), (
        "Es wird keine SHA-256 gebildet - MD5 oder SHA-1 wären wertlos.")
    assert "SHA256SUMS.txt" in block, "Die Prüfsumme wird nirgends abgelegt."
    assert re.search(r'ReadAllText\("dist\\SHA256SUMS\.txt"\) -ne \$zeile\) \{\s*\n\s*throw ',
                     block), (
        "Die geschriebene Prüfsummendatei wird nicht zurückgelesen.")


def test_release_sieht_vor_dem_hochladen_nach():
    # if-no-files-found: error greift erst, wenn gar nichts passt: Bei einer
    # Liste aus drei Pfaden fiele eine einzelne fehlende Datei nicht auf.
    block = _job(RELEASE, "windows-exe")
    assert re.search(r"if \(-not \(Test-Path \$datei\)\) \{ throw ", block), (
        "Vor dem Hochladen wird nicht geprüft, ob alle Dateien bereitliegen.")
    # Die Liste dieses Schrittes, nicht die ganze Datei: „dist\SHA256SUMS.txt"
    # steht auch im Schritt, der die Prüfsumme schreibt - daran ist dieser
    # Wächter beim Rotsetzen einmal grün geblieben.
    liste = re.search(r"foreach \(\$datei in @\((.*?)\)\) \{", block, re.DOTALL)
    assert liste, "Der Schritt sieht keine Liste von Dateien mehr durch."
    nachgesehen = re.findall(r'"dist\\([^"]+)"', liste[1])
    assert sorted(nachgesehen) == sorted(ANHAENGE), (
        f"Nachgesehen wird {sorted(nachgesehen)}, erwartet waren {sorted(ANHAENGE)}.")


def test_release_laedt_genau_die_erwarteten_dateien_hoch():
    # Wird ein Pfad aus der Liste gestrichen, entstünde ein Release ohne
    # Prüfsumme oder ohne Lizenzhinweise - und zwar grün.
    pfade = _blockliste(_job(RELEASE, "windows-exe"), "path")
    assert sorted(pfade) == sorted(f"dist/{datei}" for datei in ANHAENGE), (
        f"Hochgeladen wird {sorted(pfade)}, erwartet waren die drei Dateien "
        f"{sorted(ANHAENGE)}.")


def test_release_haengt_alles_an_den_release():
    # Dasselbe eine Stufe später: Was nicht in dieser Liste steht, fehlt am
    # Release, auch wenn es gebaut und hochgeladen wurde.
    files = _blockliste(_job(RELEASE, "release"), "files")
    namen = sorted(pfad.rsplit("/", 1)[-1] for pfad in files)
    assert namen == sorted(ANHAENGE + ["Passwort-Generator-*-quellen.zip"]), (
        f"Am Release hängen {namen} - erwartet waren EXE, Prüfsumme, "
        "Lizenzhinweise und das Quellpaket.")
    for pfad in files:
        assert pfad.startswith("artefakte/"), (
            f"{pfad} zeigt nicht in den heruntergeladenen Artefaktordner.")


def test_release_baut_aus_den_festen_versionen():
    yaml = _ohne_kommentare(RELEASE)
    zeilen = [zeile for zeile in yaml.splitlines() if "pip install" in zeile]
    assert zeilen, "Im Release-Workflow wird nichts installiert?"
    for zeile in zeilen:
        assert f"-r {BAUVERSIONEN.name}" in zeile, (
            f"Diese Zeile installiert an den festen Versionen vorbei: {zeile.strip()!r}")


def test_release_scheitert_wenn_eine_datei_fehlt():
    # Beide Actions sind von Haus aus nachsichtig: upload-artifact warnt nur,
    # und action-gh-release lässt Pfade durchgehen, die nichts treffen.
    yaml = _ohne_kommentare(RELEASE)
    assert len(re.findall(r"if-no-files-found:\s*error", yaml)) == 2, (
        "Beide Upload-Schritte brauchen if-no-files-found: error.")
    assert re.search(r"fail_on_unmatched_files:\s*true", yaml), (
        "Der Release-Schritt braucht fail_on_unmatched_files: true.")


def test_release_bleibt_zunaechst_ein_entwurf():
    # Der letzte Schritt lässt sich nie proben - er läuft nur bei einem echten
    # Tag. Als Entwurf angelegt, kann man die Anhänge vorher ansehen.
    assert re.search(r"draft:\s*true", _job(RELEASE, "release")), (
        "Der Release entsteht nicht als Entwurf.")


def test_release_wartet_auf_beide_bau_jobs():
    # Ohne needs liefe der Release-Job parallel zum Bau und fände keine
    # Artefakte - sichtbar erst beim Tag.
    treffer = re.search(r"^    needs:\s*\[([^\]]*)\]", _job(RELEASE, "release"), re.MULTILINE)
    assert treffer, "Der Release-Job wartet auf nichts."
    assert sorted(name.strip() for name in treffer[1].split(",")) == \
        ["quellpaket", "windows-exe"], (
        f"Der Release-Job wartet auf {treffer[1].strip()!r}.")


def test_release_laeuft_bei_tag_und_auf_zuruf():
    # Der Tag-Filter ist der Auslöser im Ernstfall, workflow_dispatch der
    # Probelauf. Fällt einer weg, merkt es niemand, bis man ihn braucht.
    kopf = _ohne_kommentare(RELEASE).partition("\njobs:\n")[0]
    assert re.search(r'tags:\s*\["v\*"\]', kopf), (
        "Der Workflow hört nicht mehr auf Versions-Tags.")
    assert re.search(r"^\s*workflow_dispatch:\s*$", kopf, re.MULTILINE), (
        "Ohne workflow_dispatch lässt sich die Bau-Kette nicht proben.")


def test_release_schreibt_nur_im_letzten_job():
    # Die Bau-Jobs holen fremde Abhängigkeiten und bauen eine EXE. Sie
    # brauchen kein Schreibrecht am Repository, und sie sollen keins haben.
    kopf = _ohne_kommentare(RELEASE).partition("\njobs:\n")[0]
    assert re.search(r"^permissions:\s*\n\s*contents:\s*read\s*$", kopf, re.MULTILINE), (
        "Der Workflow gibt nicht von vornherein nur Leserecht.")
    for name in ("quellpaket", "windows-exe"):
        assert "contents: write" not in _job(RELEASE, name), (
            f"Der Bau-Job {name} hat Schreibrecht am Repository.")
    assert re.search(r"^    permissions:\s*\n\s*contents:\s*write\s*$",
                     _job(RELEASE, "release"), re.MULTILINE), (
        "Der Release-Job kann ohne Schreibrecht nichts veröffentlichen.")


def test_release_legt_nur_bei_einem_tag_los():
    # Ohne Tag kennt softprops/action-gh-release keinen Namen für den Release
    # und bricht ab. Fehlt die Bedingung, wird jeder Probelauf rot, obwohl Bau
    # und Prüfungen durchgelaufen sind - und ein roter Lauf, der nichts
    # bedeutet, wird irgendwann nicht mehr angesehen.
    bedingung = re.search(r"^    if:(.*)$", _job(RELEASE, "release"), re.MULTILINE)
    assert bedingung, "Der Job, der den Release anlegt, hängt nicht an einem Tag."
    # Auf den genauen Ausdruck, nicht auf das Stichwort: Ein verdrehtes „!="
    # oder ein angehängtes „|| true" ließe den Release bei einem echten Tag
    # ausfallen oder trotzdem laufen - beides fiele erst beim Taggen auf.
    erwartet = r"""\s*(?:\$\{\{)?\s*github\.ref_type\s*==\s*['"]tag['"]\s*(?:\}\})?\s*"""
    assert re.fullmatch(erwartet, bedingung.group(1)), (
        f"Die Bedingung lautet {bedingung.group(1).strip()!r}, erwartet war "
        "genau github.ref_type == 'tag'.")
    for name in ("quellpaket", "windows-exe"):
        assert not re.search(r"^    if:", _job(RELEASE, name), re.MULTILINE), (
            f"Der Job {name} darf nicht an einem Tag hängen, sonst baut und "
            "prüft der Probelauf gar nichts mehr.")


# --- Was dem Anwender zugesagt wird ---------------------------------------

def test_sicherheitsdatei_nennt_die_aktuelle_reihe(pg):
    # „Gepflegt wird die neueste Version" ist nichts wert, wenn dort die Reihe
    # von vorgestern steht - oder ein „nein" daneben.
    haupt, neben = pg.VERSION.split(".")[:2]
    reihe = f"{haupt}.{neben}.x"
    treffer = re.search(rf"^\|\s*{re.escape(reihe)}\s*\|\s*([^|]+?)\s*\|",
                        SICHERHEIT.read_text(encoding="utf-8"), re.MULTILINE)
    assert treffer, f"SECURITY.md nennt {reihe} nicht - dort steht eine ältere Reihe."
    assert treffer[1].lower() == "ja", (
        f"SECURITY.md führt {reihe} als {treffer[1]!r} - die aktuelle Reihe "
        "wird aber gepflegt.")


@pytest.mark.parametrize("readme", READMES, ids=lambda pfad: pfad.name)
def test_erststart_hinweis_steht_in_beiden_readmes(readme):
    # Die EXE ist nicht signiert: SmartScreen meldet sich, und ein Virenschutz
    # hält die frische Datei kurz fest. Wer das nicht liest, hält das Programm
    # für kaputt. Die Prüfsumme liegt als Datei am Release - wer in den
    # Release-Notizen danach sucht, findet nichts.
    text = readme.read_text(encoding="utf-8")
    assert "SmartScreen" in text, f"{readme.name} warnt nicht vor SmartScreen."
    assert "SHA-256" in text, f"{readme.name} nennt die Prüfsumme nicht."
    assert "SHA256SUMS.txt" in text, (
        f"{readme.name} sagt nicht, wo die Prüfsumme steht.")


def test_sicherheitsdatei_verweist_auf_die_pruefsummendatei():
    text = SICHERHEIT.read_text(encoding="utf-8")
    assert "SHA256SUMS.txt" in text, (
        "SECURITY.md sagt nicht, wogegen die Summe zu prüfen ist.")

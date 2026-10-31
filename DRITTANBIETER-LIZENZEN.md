# Lizenzen der Fremdkomponenten

Der Quellcode des Passwort-Generators steht unter der MIT-Lizenz – siehe
[LICENSE](LICENSE). Diese Datei listet die Bestandteile anderer Projekte auf, die in der
fertigen **Windows-EXE** mitgeliefert werden, und sagt, was daraus folgt.

*English version below – [Licenses of third-party components](#licenses-of-third-party-components).*

## Das Wichtigste in vier Sätzen

- **Der Quellcode bleibt MIT.** Daran ändert diese Datei nichts.
- **Das Skript** `Passwort-Generator.pyw` liefert gar nichts mit: Es kommt mit der
  Standardbibliothek aus, es gibt keine Pakete zu installieren.
- **Die Windows-EXE** enthält zusätzlich die Python-Laufzeit, Tcl/Tk für die Oberfläche
  und einige Bibliotheken, die der Windows-Build von Python mitbringt – alle unter
  permissiven Lizenzen.
- **Auch die EXE darf als MIT-Werk weitergegeben werden.** Copyleft steckt nur im
  Bootloader von PyInstaller, und dessen Lizenz nimmt damit erzeugte Programme
  ausdrücklich aus.

### Warum die EXE MIT bleiben darf

PyInstaller steht unter der GPLv2, enthält aber eine Ausnahme: Programme, die *mit*
PyInstaller gepackt werden, dürfen unter beliebigen Bedingungen weitergegeben werden –
sonst stünde jede damit gebaute Anwendung unter der GPL. Die übrigen Bestandteile stehen
unter PSF, BSD, MIT, Apache-2.0 oder der zlib-Lizenz; keiner von ihnen verlangt, dass das
Gesamtwerk unter dieselbe Lizenz gestellt wird. Alle verlangen jedoch, dass ihr
Lizenztext und ihr Urhebervermerk mitgeliefert werden – dafür gibt es diese Datei.

## Was in der Windows-EXE steckt

Die Angaben stammen aus der gebauten Datei selbst (die mitgelieferten `.dll` und `.pyd`
lassen sich darin nachlesen) und gelten für den Bau mit den Versionen aus
[requirements-build.txt](requirements-build.txt). Die Fehlerbehebungsstände folgen dem
Python-Build des Bau-Rechners und können sich von Release zu Release unterscheiden.

| Bestandteil | Lizenz | Lizenztext und Quelle |
|---|---|---|
| **Python** 3.14 – Laufzeit und Standardbibliothek (`python314.dll`) | PSF License 2.0 | [docs.python.org](https://docs.python.org/3/license.html) |
| **Tcl/Tk** 9.0 – die Oberfläche (`tcl90.dll`, `tcl9tk90.dll`) | Tcl/Tk-Lizenz (BSD-artig) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **libtommath** – große Zahlen für Tcl (`libtommath.dll`) | public domain (Unlicense) | [LICENSE](https://github.com/libtom/libtommath/blob/develop/LICENSE) |
| **OpenSSL** 3.5 – Prüfsummen und TLS, kommt mit `hashlib` und `ssl` (`libcrypto-3.dll`, `libssl-3.dll`) | Apache License 2.0 | [openssl-library.org](https://openssl-library.org/source/license/) |
| **libffi** – fremde Funktionen aufrufen, kommt mit `ctypes` (`libffi-8.dll`) | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **zlib-ng** 1.3.1 – Packen, kommt mit `zlib` (`zlib1.dll`) | zlib-Lizenz | [LICENSE.md](https://github.com/zlib-ng/zlib-ng/blob/develop/LICENSE.md) |
| **bzip2** – Packen, kommt mit `bz2` (`_bz2.pyd`) | BSD-artig (bzip2-Lizenz) | [COPYING](https://gitlab.com/bzip2/bzip2/-/blob/master/COPYING) |
| **XZ Utils** – Packen, kommt mit `lzma` (`_lzma.pyd`) | 0BSD | [COPYING](https://github.com/tukaani-project/xz/blob/master/COPYING) |
| **Zstandard** 1.5.7 – Packen, kommt mit `compression.zstd` (`_zstd.pyd`) | BSD 3-Clause (wahlweise GPLv2) | [LICENSE](https://github.com/meta/zstd/blob/dev/LICENSE) |
| **PyInstaller** – dessen Bootloader startet die gepackte Anwendung | GPLv2 **mit** Ausnahme für damit erzeugte Programme | [Lizenzhinweis](https://pyinstaller.org/en/stable/license.html) |

### Was davon das Programm wirklich benutzt

Nur Tcl/Tk und die Standardbibliothek. Prüfsummen, TLS und die Packformate wandern mit,
weil PyInstaller die Standardbibliothek vollständig einpackt – das Programm ruft sie
nicht auf und baut **keine** Netzwerkverbindungen auf, auch nicht über das mitgelieferte
OpenSSL. Aufgeführt sind sie trotzdem: Entscheidend ist, was in der Datei liegt, nicht
was davon läuft.

Der Windows-Build von Python bringt diese Bibliotheken von sich aus mit. Die
[Lizenzseite von Python](https://docs.python.org/3/license.html) führt sie im Abschnitt
*Licenses and Acknowledgements for Incorporated Software* mit vollständigen Lizenztexten
auf.

### Nicht aufgeführt: Systembibliotheken von Windows

Dateien wie `VCRUNTIME140.dll`, `ucrtbase.dll` oder die `api-ms-win-*`-Bibliotheken
gehören zum Betriebssystem beziehungsweise zu dessen Laufzeitumgebung und werden hier
nicht einzeln aufgeführt.

### Quellcode

Der Quellcode aller oben genannten Komponenten liegt öffentlich bei den verlinkten
Projekten. Der Quellcode des Passwort-Generators selbst ist eine einzige lesbare Datei:
`Passwort-Generator.pyw`, zu jeder Version als Quellpaket am [Release](../../releases)
und im Verlauf dieses Repositorys.

## Pflege dieser Datei

Kommt eine Komponente hinzu oder fällt eine weg, gehört das hier hinein. Der Test
`tests/test_verpackung.py` prüft, dass jeder Bestandteil in **beiden** Sprachen eine
Tabellenzeile mit seiner Lizenz hat und dass diese Datei dem Release wirklich beiliegt –
er schlägt fehl, wenn das vergessen wird.

---

# Licenses of third-party components

The source code of Passwort-Generator is under the MIT License – see
[LICENSE](LICENSE). This file lists the third-party components shipped inside the
**Windows executable** and explains what follows from that.

## The essentials in four sentences

- **The source code stays MIT.** This file changes nothing about that.
- **The script** `Passwort-Generator.pyw` ships nothing at all: it runs on the standard
  library, there are no packages to install.
- **The Windows executable** additionally contains the Python runtime, Tcl/Tk for the
  interface and a few libraries that the Windows build of Python brings along – all
  under permissive licenses.
- **The executable may be redistributed as an MIT work as well.** The only copyleft part
  is the PyInstaller bootloader, and its license explicitly exempts programs built with
  it.

### Why the executable may stay MIT

PyInstaller is licensed under the GPLv2 but carries an exception: software packaged
*with* PyInstaller may be distributed under terms of your choosing – otherwise every
application built with it would fall under the GPL. The remaining components are under
PSF, BSD, MIT, Apache-2.0 or the zlib license; none of them requires the work as a whole
to use the same license. All of them do require their license text and copyright notice
to be shipped along – that is what this file is for.

## What is inside the Windows executable

The list was taken from the built file itself (the bundled `.dll` and `.pyd` files can be
read from it) and applies to a build with the versions pinned in
[requirements-build.txt](requirements-build.txt). Patch levels follow the Python build on
the build machine and may differ between releases.

| Component | License | License text and source |
|---|---|---|
| **Python** 3.14 – runtime and standard library (`python314.dll`) | PSF License 2.0 | [docs.python.org](https://docs.python.org/3/license.html) |
| **Tcl/Tk** 9.0 – the user interface (`tcl90.dll`, `tcl9tk90.dll`) | Tcl/Tk license (BSD-style) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **libtommath** – big numbers for Tcl (`libtommath.dll`) | public domain (Unlicense) | [LICENSE](https://github.com/libtom/libtommath/blob/develop/LICENSE) |
| **OpenSSL** 3.5 – hashes and TLS, ships with `hashlib` and `ssl` (`libcrypto-3.dll`, `libssl-3.dll`) | Apache License 2.0 | [openssl-library.org](https://openssl-library.org/source/license/) |
| **libffi** – calling foreign functions, ships with `ctypes` (`libffi-8.dll`) | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **zlib-ng** 1.3.1 – compression, ships with `zlib` (`zlib1.dll`) | zlib license | [LICENSE.md](https://github.com/zlib-ng/zlib-ng/blob/develop/LICENSE.md) |
| **bzip2** – compression, ships with `bz2` (`_bz2.pyd`) | BSD-style (bzip2 license) | [COPYING](https://gitlab.com/bzip2/bzip2/-/blob/master/COPYING) |
| **XZ Utils** – compression, ships with `lzma` (`_lzma.pyd`) | 0BSD | [COPYING](https://github.com/tukaani-project/xz/blob/master/COPYING) |
| **Zstandard** 1.5.7 – compression, ships with `compression.zstd` (`_zstd.pyd`) | BSD 3-Clause (or GPLv2, at your option) | [LICENSE](https://github.com/meta/zstd/blob/dev/LICENSE) |
| **PyInstaller** – its bootloader starts the packaged application | GPLv2 **with** an exception for programs built with it | [license notice](https://pyinstaller.org/en/stable/license.html) |

### What the program actually uses

Only Tcl/Tk and the standard library. Hashes, TLS and the compression formats come along
because PyInstaller bundles the whole standard library – the program never calls them and
makes **no** network connections, not through the bundled OpenSSL either. They are listed
regardless: what matters is what sits in the file, not what of it runs.

The Windows build of Python brings these libraries along by itself. Python's
[license page](https://docs.python.org/3/license.html) lists them with their full license
texts under *Licenses and Acknowledgements for Incorporated Software*.

### Not listed: Windows system libraries

Files such as `VCRUNTIME140.dll`, `ucrtbase.dll` or the `api-ms-win-*` libraries belong
to the operating system or its runtime environment and are not listed individually here.

### Source code

The source code of every component above is publicly available from the linked projects.
The source code of Passwort-Generator itself is a single readable file,
`Passwort-Generator.pyw`, attached to every [release](../../releases) as a source package
and kept in this repository's history.

## Keeping this file current

When a component is added or dropped, it belongs in here. The test
`tests/test_verpackung.py` checks that every component has a table row naming its license
in **both** languages and that this file really is attached to the release – it fails if
that is forgotten.

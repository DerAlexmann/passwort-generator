# Sicherheit

## Eine Lücke melden

Bitte **kein öffentliches Issue** für Sicherheitslücken. Melde sie über
GitHub: Reiter **Security** → **Report a vulnerability**
([private Sicherheitsmeldung](../../security/advisories/new)). Die Meldung ist
nur für die Projektbetreuung sichtbar.

Hilfreich sind: eine Beschreibung des Problems, die Version des Programms (sie
steht in der Kopfzeile und auf dem Reiter „Info & Copyright"), das
Betriebssystem und, wenn möglich, eine Anleitung zum Nachstellen.

Eine Antwort kommt in der Regel innerhalb einer Woche.

## Unterstützte Versionen

Gepflegt wird jeweils die neueste veröffentlichte Version.

| Version | Unterstützt |
|---|---|
| 1.1.x | ja |
| älter | nein |

## Wie das Programm mit Passwörtern umgeht

- **Erzeugt** werden sie mit `secrets`, dem Zufallsgenerator des
  Betriebssystems, der für Passwörter und Schlüssel vorgesehen ist – nicht mit
  `random`.
- **Gespeichert** wird ein Passwort nirgends: weder in der Einstellungsdatei
  noch sonst auf der Festplatte. Es lebt im Speicher des laufenden Programms
  und verschwindet mit dem Schließen des Fensters. In `passwort-generator.json`
  stehen nur Länge, Zeichenauswahl, Sprache, Farbschema und Fensterlage.
- **Übertragen** wird nichts. Das Programm baut keine Netzwerkverbindungen auf
  und lädt nichts nach.
- **In die Zwischenablage** gelangt das Passwort nur auf ausdrücklichen Wunsch,
  per Schalter oder `Strg`+`C`. Was dort liegt, können andere Programme lesen –
  das ist der Sinn der Zwischenablage. Ein Passwortmanager ist der sicherere
  Weg, ein Passwort aufzubewahren.
- **Auf dem Bildschirm** steht das erzeugte Passwort offen lesbar. Wer über die
  Schulter schauen kann, kann es mitlesen.

## Die veröffentlichte EXE

Die EXE ist nicht signiert. Prüfe nach dem Herunterladen die SHA-256-Summe
gegen die Angabe in den Release-Notizen:

```powershell
Get-FileHash .\Passwort-Generator.exe -Algorithm SHA256
```

Wer lieber nichts Fertiges ausführt: Das Programm ist eine einzige lesbare
Python-Datei und lässt sich mit `build.cmd` selbst bauen.

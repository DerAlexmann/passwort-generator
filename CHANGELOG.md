# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

## [1.1.0] – 2026-09-17

### Hinzugefügt

- Das Kopieren in die Zwischenablage wird jetzt unter dem Passwort grün
  bestätigt. Die Bestätigung nimmt sich nach drei Sekunden von selbst zurück;
  ein neues Passwort beendet sie sofort.

### Behoben

- Der Ablageort der Einstellungsdatei auf dem Reiter „Info & Copyright" stand
  in einer Zeile ohne Umbruch und zog das Fenster so breit, wie der Pfad lang
  war. Liegt das Programm in einem tief verschachtelten Ordner, war das
  Fenster deutlich zu breit. Der Pfad bricht jetzt um, die Fenstergröße hängt
  nicht mehr vom Ablageort ab.

## [1.0.0] – 2026-09-17

Erste Fassung.

- Länge von 4 bis 64 Zeichen am Schieberegler, in Einerschritten.
- Farbige Stärkeanzeige: rot bis 8 Zeichen, gelb bei 9 und 10, grün ab 11.
- Zeichenauswahl per Haken: Großbuchstaben, Kleinbuchstaben, Ziffern, Satz-
  und Sonderzeichen. Jede angehakte Gruppe kommt mindestens einmal vor,
  solange die Länge dafür reicht.
- Passwörter aus dem Zufallsgenerator des Betriebssystems (`secrets`).
- Kopieren in die Zwischenablage, Erzeugen mit `F5`, Kopieren mit `Strg`+`C`.
- Deutsch und Englisch, helles und dunkles Schema – umschaltbar, ohne dass
  sich Fenstergröße, Fensterlage oder der gewählte Reiter ändern.
- Länge, Zeichenauswahl, Sprache, Schema und Fensterlage bleiben bis zum
  nächsten Start erhalten. Ohne Einstellungsdatei startet das Fenster in der
  Bildschirmmitte.

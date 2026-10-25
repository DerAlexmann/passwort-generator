# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

## [1.3.1] – 2026-10-25

### Behoben

- Fehler aus einem Tk-Rückruf verschwanden spurlos. Tk schickt sie nach
  `sys.stderr`, und das gibt es in einem `.pyw`-Fenster nicht; auf dem
  Bildschirm konnte dabei eine Anzeige stehen bleiben, die nicht mehr
  stimmte. Sie stehen jetzt rot in der Statuszeile. Genannt wird nur die
  Art des Fehlers – seine Meldung könnte das geprüfte Passwort enthalten.
- Scheitert die Bewertung eines eingegebenen Passworts, bleibt kein altes
  Urteil stehen: Balken und Stufe gehen zurück, die Zeile meldet „Die
  Prüfung ist fehlgeschlagen“.
- Die Tk-Variablen hängen jetzt ausdrücklich am Fenster des Programms und
  nicht mehr an der Standard-Wurzel von Tkinter. Sonst ginge ein Fehler aus
  ihrem Rückruf an die Fehlerbehandlung eines fremden Fensters.

## [1.3.0] – 2026-10-25

### Hinzugefügt

- Der neue Reiter „Prüfen“ bewertet ein selbst eingegebenes Passwort nach
  demselben Maßstab wie das erzeugte: Länge mal Zeichenvorrat, in Bit, mit
  denselben Grenzen bei 55 und 70 Bit. Der Zeichenvorrat ist hier nicht
  bekannt und wird aus den vorkommenden Zeichen geschätzt – eine Ziffer im
  Passwort heißt, dass alle zehn Ziffern möglich waren; Zeichen außerhalb
  der vier Gruppen zählen einzeln. Das Eingegebene wird nicht gespeichert,
  nicht in die Einstellungsdatei geschrieben und nicht übertragen; ein
  Schalter leert das Feld. Vorschläge macht der Reiter keine.
- Auf dem Reiter „Prüfen“ legt `Strg`+`C` nicht mehr das erzeugte Passwort
  der anderen Seite in die Zwischenablage – samt Erfolgsmeldung, die man
  dort gar nicht zu sehen bekam. Im Prüffeld kopiert die Tastenkombination
  wie gewohnt die eigene Markierung.

### Behoben

- Ein Stärkebalken ohne Bit zeigte links einen roten Strich von einem
  Pixel. Er bleibt jetzt leer – zu sehen war das bisher, wenn man alle
  Zeichengruppen abwählte.

## [1.2.0] – 2026-10-11

### Geändert

- Die Stärkeanzeige bewertet jetzt den Zufall im Passwort in Bit statt
  allein die Länge. Bisher war alles ab 11 Zeichen grün, egal aus wie
  vielen Zeichen gewürfelt wurde – 11 Ziffern (37 Bit) sahen damit so
  stark aus wie 11 Zeichen aus allen vier Gruppen (72 Bit). Rot ist jetzt
  alles unter 55 Bit, gelb bis 70 Bit, grün darüber. Mit allen vier
  Gruppen bleiben die Grenzen dieselben wie vorher – rot bis 8 Zeichen,
  gelb bei 9 und 10, grün ab 11; kleine Zeichenvorräte werden aber nicht
  mehr zu gut bewertet. Aus Ziffern allein braucht es nun 22 Zeichen für
  grün.
- Die Fußzeile nennt neben dem Zeichenvorrat auch die erreichten Bit, und
  der Balken folgt ihnen: Er ist bei 100 Bit voll, nicht mehr erst bei 64
  Zeichen. Der Reiter „Erklärungen“ beschreibt die neuen Grenzen.

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

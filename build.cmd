@echo off
REM ---------------------------------------------------------------------
REM Baut Passwort-Generator.exe neu; das Ergebnis liegt anschliessend in
REM dist\Passwort-Generator.exe.
REM
REM Voraussetzung:  pip install -r requirements-build.txt
REM                (genaue Versionen - derselbe Stand wie im Release)
REM Das Symbol entsteht bei Bedarf mit:  python icon_erzeugen.py
REM ---------------------------------------------------------------------
setlocal

REM Python finden: bevorzugt ueber den Windows-Starter py, sonst python
set "PY=py -3"
py -3 --version >nul 2>nul || set "PY=python"

REM Versionsangaben fuer die EXE erzeugen: Ohne --version-file bleiben
REM Produktname, Version und Urheber in den Dateieigenschaften leer.
%PY% versionsinfo_erzeugen.py
if errorlevel 1 (
  echo.
  echo Die Versionsangaben liessen sich nicht erzeugen - siehe Meldung oben.
  pause
  exit /b 1
)

%PY% -m PyInstaller --noconfirm --onefile --windowed --clean ^
  --name "Passwort-Generator" ^
  --icon "passwort_generator.ico" ^
  --version-file "versionsinfo.txt" ^
  "Passwort-Generator.pyw"

if errorlevel 1 (
  echo.
  echo Der Bau ist fehlgeschlagen. Fehlt PyInstaller?
  echo     pip install -r requirements-build.txt
  pause
  exit /b 1
)

REM Die Lizenzen der mitgelieferten Komponenten gehoeren neben die EXE -
REM wer nur die Datei weitergibt, gibt sie sonst ohne Lizenzangaben weiter.
copy /y "DRITTANBIETER-LIZENZEN.md" "dist\" >nul
if errorlevel 1 (
  echo.
  echo Die Lizenzhinweise liessen sich nicht neben die EXE legen.
  echo Die EXE darf ohne sie nicht weitergegeben werden.
  pause
  exit /b 1
)

echo.
echo Fertig: dist\Passwort-Generator.exe
echo         dist\DRITTANBIETER-LIZENZEN.md
pause

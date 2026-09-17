@echo off
REM ---------------------------------------------------------------------
REM Baut Passwort-Generator.exe neu; das Ergebnis liegt anschliessend in
REM dist\Passwort-Generator.exe.
REM
REM Voraussetzung:  pip install pyinstaller
REM Das Symbol entsteht bei Bedarf mit:  python icon_erzeugen.py
REM ---------------------------------------------------------------------
setlocal

REM Python finden: bevorzugt ueber den Windows-Starter py, sonst python
set "PY=py -3"
py -3 --version >nul 2>nul || set "PY=python"

%PY% -m PyInstaller --noconfirm --onefile --windowed --clean ^
  --name "Passwort-Generator" ^
  --icon "passwort_generator.ico" ^
  "Passwort-Generator.pyw"

if errorlevel 1 (
  echo.
  echo Der Bau ist fehlgeschlagen. Fehlt PyInstaller?
  echo     pip install pyinstaller
  pause
  exit /b 1
)

echo.
echo Fertig: dist\Passwort-Generator.exe
pause

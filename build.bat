@echo off
setlocal

set "PYTHON_EXE=venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Virtual environment python not found: %PYTHON_EXE%
    exit /b 1
)

echo Building Photo Analyzer Executable...
"%PYTHON_EXE%" -m pip install pyinstaller
if errorlevel 1 exit /b 1

REM Remove old artifacts to avoid stale packaged modules.
if exist build rmdir /s /q build
if exist dist\PhotoAnalyzer rmdir /s /q dist\PhotoAnalyzer
if exist dist\PhotoAnalyzer.zip del /q dist\PhotoAnalyzer.zip

REM Build the executable using PyInstaller
REM --noconfirm: overwrite existing build/dist
REM --windowed: no console window
REM --name: app name
REM --clean: remove old analysis cache to avoid stale module states
REM --exclude-module matplotlib: prevent startup crash from bundled matplotlib internals
REM --add-data: bundle custom app font for consistent UI
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --windowed --exclude-module matplotlib --add-data "assets\\fonts\\NotoSansKR-VF.ttf;assets\\fonts" --name "PhotoAnalyzer" app.py
if errorlevel 1 exit /b 1

REM Zip the whole folder so the EXE and _internal files stay together when shared.
powershell -NoProfile -Command "Compress-Archive -Path 'dist\\PhotoAnalyzer\\*' -DestinationPath 'dist\\PhotoAnalyzer.zip' -Force"
if errorlevel 1 exit /b 1

echo.
echo Build complete.
echo Run: dist\PhotoAnalyzer\PhotoAnalyzer.exe
echo Share: dist\PhotoAnalyzer.zip
echo Important: copy the whole dist\PhotoAnalyzer folder or the zip, not the EXE alone.

@echo off
echo Building Photo Analyzer Executable...
call venv\Scripts\activate
pip install pyinstaller

REM Remove old artifacts to avoid stale packaged modules.
if exist build rmdir /s /q build
if exist dist\PhotoAnalyzer rmdir /s /q dist\PhotoAnalyzer

REM Build the executable using PyInstaller
REM --noconfirm: overwrite existing build/dist
REM --windowed: no console window
REM --name: app name
REM --clean: remove old analysis cache to avoid stale module states
REM --exclude-module matplotlib: prevent startup crash from bundled matplotlib internals
REM --add-data: bundle custom app font for consistent UI
pyinstaller --noconfirm --clean --windowed --exclude-module matplotlib --add-data "assets\\fonts\\NotoSansKR-VF.ttf;assets\\fonts" --name "PhotoAnalyzer" app.py

echo Build complete. The executable is located in the dist\PhotoAnalyzer folder.
pause

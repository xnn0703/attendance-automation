@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === install PyInstaller (skip if present) ===
python -m pip install -q pyinstaller
echo === building (PySide6 is large, please wait 1-3 min) ===
pyinstaller --noconfirm mingxu.spec
echo.
echo === done: dist\mingxu.exe ===
pause

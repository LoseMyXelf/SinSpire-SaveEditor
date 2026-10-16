@echo off
cd /d "%~dp0"
py -3 save_editor_gui.py
if errorlevel 1 pause

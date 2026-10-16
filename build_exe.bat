@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Project virtual environment not found. Follow README.md setup steps first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath dist --workpath build SinSpireSaveEditor.spec
if errorlevel 1 goto failed
echo.
echo Build complete: dist\Sin Spire Save Editor.exe
pause
exit /b 0
:failed
echo.
echo Build failed. See the message above for details.
pause
exit /b 1

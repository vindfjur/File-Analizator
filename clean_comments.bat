@echo off
rem Remove comments and docstrings from the project source (Windows).
chcp 65001 >nul
cd /d "%~dp0"

rem Use the project's local Python if the venv exists
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

"%PY%" "scripts\strip_comments.py"

echo.
echo Done. Restore comments with:  git checkout -- .
pause

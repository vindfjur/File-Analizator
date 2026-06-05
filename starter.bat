@echo off
setlocal

cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\build_app.py %*
) else (
  python scripts\build_app.py %*
)
if errorlevel 1 (
  echo.
  echo Стартер завершился с ошибкой.
  echo Проверьте текст выше. Часто помогает запустить этот файл повторно после установки Python.
  pause
  exit /b %errorlevel%
)

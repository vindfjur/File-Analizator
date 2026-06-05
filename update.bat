@echo off
setlocal EnableExtensions

title File-Analizator updater

set "REPO_URL=https://github.com/vindfjur/File-Analizator/archive/refs/heads/main.zip"
set "APP_NAME=File-Analizator"
set "RUN_DIR=%CD%"
set "TEMP_DIR=%TEMP%\%APP_NAME%_update_%RANDOM%%RANDOM%"
set "ZIP_FILE=%TEMP_DIR%\source.zip"
set "EXTRACT_DIR=%TEMP_DIR%\extract"
set "SOURCE_DIR=%EXTRACT_DIR%\File-Analizator-main"

echo ============================================================
echo   Downloading the latest %APP_NAME% version
echo ============================================================
echo Target folder: %RUN_DIR%
echo.

echo [1/5] Checking PowerShell...
where powershell >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PowerShell was not found.
    goto fail
)

echo [2/5] Preparing temporary folder...
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%" >nul 2>nul
mkdir "%EXTRACT_DIR%" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Could not create the temporary folder:
    echo %TEMP_DIR%
    goto fail
)

echo [3/5] Downloading archive from GitHub...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%REPO_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing" >nul
if errorlevel 1 (
    echo [ERROR] Could not download the archive. Check internet access and GitHub availability.
    goto fail
)
if not exist "%ZIP_FILE%" (
    echo [ERROR] The archive file was not created after download.
    goto fail
)

echo [4/5] Extracting archive...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force" >nul
if errorlevel 1 (
    echo [ERROR] Could not extract the archive.
    goto fail
)
if not exist "%SOURCE_DIR%" (
    echo [ERROR] Expected folder was not found in the archive: File-Analizator-main
    goto fail
)

echo [5/5] Overwriting current folder...
robocopy "%SOURCE_DIR%" "%RUN_DIR%" /E /NFL /NDL /NJH /NJS /NP >nul
set "ROBOCOPY_CODE=%ERRORLEVEL%"
if %ROBOCOPY_CODE% GEQ 8 (
    echo [ERROR] Robocopy failed. Code: %ROBOCOPY_CODE%
    goto fail
)

call :cleanup
echo.
echo ============================================================
echo [OK] Done. Current folder was updated:
echo %RUN_DIR%
echo ============================================================
echo.
echo Press any key to exit...
pause >nul
exit /b 0

:fail
set "FAIL_CODE=%ERRORLEVEL%"
if "%FAIL_CODE%"=="0" set "FAIL_CODE=1"
echo.
echo ============================================================
echo [ERROR] Update stopped.
echo ============================================================
call :cleanup
echo.
echo Press any key to exit...
pause >nul
exit /b %FAIL_CODE%

:cleanup
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%" >nul 2>nul
exit /b 0

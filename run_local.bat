@echo off
setlocal

if not "%~1"=="" set "TOURNAMENT_PATH=%~f1"
cd /d "%~dp0"
set "PYTHONPATH=src"

if "%~1"=="" (
    if not exist ".tmp\demo.tgo.json" (
        if not exist ".tmp" mkdir ".tmp"
        python -m pairing.cli.main demo ".tmp\demo.tgo.json"
        if errorlevel 1 exit /b 1
    )
    set "TOURNAMENT_PATH=.tmp\demo.tgo.json"
) else (
    rem TOURNAMENT_PATH already normalized before changing directories.
)

python -m pairing.cli.main web "%TOURNAMENT_PATH%" --host 127.0.0.1 --port 8123 --open-browser
exit /b %ERRORLEVEL%

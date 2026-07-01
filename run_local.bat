@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=src"

if "%~1"=="" (
    if not exist ".tmp\demo.tgo.json" (
        if not exist ".tmp" mkdir ".tmp"
        python -m pairing.cli.main demo ".tmp\demo.tgo.json"
        if errorlevel 1 exit /b 1
    )
    set "TOURNAMENT_FILE=.tmp\demo.tgo.json"
) else (
    set "TOURNAMENT_FILE=%~1"
)

python -m pairing.cli.main web "%TOURNAMENT_FILE%" --host 127.0.0.1 --port 8123 --open-browser
exit /b %ERRORLEVEL%

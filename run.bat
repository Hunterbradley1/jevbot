@echo off
setlocal
cd /d "%~dp0"

rem Prefer the Windows "py" launcher, fall back to "python"
where py >nul 2>nul && (set "PYTHON=py -3") || (set "PYTHON=python")

%PYTHON% --version >nul 2>nul
if errorlevel 1 (
    echo Python 3.10+ is required. Install it from https://www.python.org/downloads/
    goto :fail
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example.
    echo Fill in TYPESAFE_API_KEY and DISCORD_BOT_TOKEN, save it, then run this again.
    start "" notepad ".env"
    goto :fail
)

%PYTHON% -c "import discord, dotenv, PIL, typesafe_sdk" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    %PYTHON% -m pip install discord.py python-dotenv pillow typesafe-sdk
    if errorlevel 1 goto :fail
)

echo Starting jevbot. Press Ctrl+C to stop.
%PYTHON% jev_bot.py
if errorlevel 1 goto :fail
exit /b 0

:fail
pause
exit /b 1

@echo off
echo ==================================
echo AI Video Generation Macro Setup
echo ==================================

REM Check Python version
echo.
echo Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
python --version
echo + Python is installed

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
echo + Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo + Virtual environment activated

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo + Pip upgraded

REM Install requirements
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo + Dependencies installed

REM Create output directory
echo.
echo Creating output directory...
if not exist output mkdir output
echo + Output directory created

REM Install FFmpeg
echo.
echo ==================================
echo Installing FFmpeg...
echo ==================================

REM Check if FFmpeg is already installed
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo + FFmpeg is already installed!
    ffmpeg -version | findstr "ffmpeg version"
    goto :skip_ffmpeg
)

echo FFmpeg not found. Installing...

REM Try chocolatey first
choco --version >nul 2>&1
if %errorlevel% equ 0 (
    echo + Chocolatey found! Installing FFmpeg via Chocolatey...
    choco install ffmpeg -y
    if %errorlevel% equ 0 (
        echo + FFmpeg installed successfully via Chocolatey!
        goto :skip_ffmpeg
    )
)

REM Manual installation if chocolatey failed or not available
echo Chocolatey not available. Installing FFmpeg manually...
echo.
echo Downloading FFmpeg (this may take a minute)...

REM Create temp directory for download
if not exist temp mkdir temp

REM Download FFmpeg using PowerShell
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'temp\ffmpeg.zip' }"

if %errorlevel% neq 0 (
    echo ! Failed to download FFmpeg
    echo ! Please manually install FFmpeg:
    echo !   1. Download from: https://www.gyan.dev/ffmpeg/builds/
    echo !   2. Extract to C:\ffmpeg\
    echo !   3. Add C:\ffmpeg\bin to your system PATH
    goto :skip_ffmpeg
)

echo + Download complete! Extracting...

REM Extract FFmpeg
powershell -Command "& { Expand-Archive -Path 'temp\ffmpeg.zip' -DestinationPath 'temp' -Force }"

REM Find the extracted folder (it has a version number in the name)
for /d %%i in (temp\ffmpeg-*) do set FFMPEG_DIR=%%i

REM Create C:\ffmpeg if it doesn't exist
if not exist C:\ffmpeg mkdir C:\ffmpeg

REM Copy ffmpeg.exe, ffprobe.exe, ffplay.exe to C:\ffmpeg\bin
if not exist C:\ffmpeg\bin mkdir C:\ffmpeg\bin
copy "%FFMPEG_DIR%\bin\ffmpeg.exe" C:\ffmpeg\bin\ >nul
copy "%FFMPEG_DIR%\bin\ffprobe.exe" C:\ffmpeg\bin\ >nul
copy "%FFMPEG_DIR%\bin\ffplay.exe" C:\ffmpeg\bin\ >nul

echo + FFmpeg extracted to C:\ffmpeg\bin

REM Add to PATH for current session
set PATH=%PATH%;C:\ffmpeg\bin

REM Add to system PATH permanently (requires admin, will prompt)
echo.
echo Adding FFmpeg to system PATH...
echo ! This may require administrator privileges (you'll see a UAC prompt)
powershell -Command "Start-Process powershell -ArgumentList '-Command \"[Environment]::SetEnvironmentVariable(''Path'', [Environment]::GetEnvironmentVariable(''Path'', ''Machine'') + '';C:\ffmpeg\bin'', ''Machine'')\"' -Verb RunAs" 2>nul

if %errorlevel% neq 0 (
    echo ! Could not add to system PATH automatically
    echo ! You may need to add C:\ffmpeg\bin to your PATH manually
    echo ! Or run this script as Administrator
)

REM Cleanup temp files
echo + Cleaning up temporary files...
rmdir /s /q temp 2>nul

echo + FFmpeg installation complete!
echo ! Please restart your terminal/IDE for PATH changes to take effect

:skip_ffmpeg

REM Copy example config if config.json doesn't exist
if not exist config.json (
    echo.
    echo Creating config.json from template...
    copy config.example.json config.json
    echo + config.json created
    echo ! Please edit config.json with your API keys and settings
) else (
    echo.
    echo + config.json already exists
)

echo.
echo ==================================
echo Setup Complete!
==================================
echo.
echo Next steps:
echo 1. Edit config.json with your API keys and settings
echo 2. Create your character folders in: Talking people/
echo    - Each folder should have: talking_personX.mp4 and images
echo 3. Run the macro: python ai_video_generation_macro.py
echo.
echo To test FFmpeg only (skip AI generation):
echo   python ai_video_generation_macro.py --test
echo.
echo To activate the virtual environment in the future:
echo   venv\Scripts\activate.bat
echo.
echo ! IMPORTANT: If FFmpeg was just installed, restart your terminal
echo !            or run: set PATH=%PATH%;C:\ffmpeg\bin
echo.
pause

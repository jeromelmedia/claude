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
echo ==================================
echo.
echo Next steps:
echo 1. Edit config.json with your API keys and settings
echo 2. Add your talking_person.mp4 video file
echo 3. Install CapCut from https://www.capcut.com/
echo 4. Install FFmpeg from https://ffmpeg.org/download.html
echo 5. Run the macro: python ai_video_generation_macro.py
echo.
echo To activate the virtual environment in the future:
echo   venv\Scripts\activate.bat
echo.
pause

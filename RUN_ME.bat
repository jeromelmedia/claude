@echo off
echo ========================================
echo AI VIDEO GENERATION MACRO
echo ========================================
echo.
echo This will automatically install dependencies and run the macro.
echo.
pause

python run_video_macro.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo ERROR OCCURRED
    echo ========================================
    pause
    exit /b 1
)

pause

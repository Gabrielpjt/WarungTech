@echo off
echo ========================================
echo WarungTech AI API Testing Suite
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import requests, json, time" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install requests
)

echo.
echo Starting AI API tests...
echo.

REM Run the test suite
python test_api_prompts.py %*

echo.
echo Testing complete!
pause
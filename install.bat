@echo off
REM Boussinesq Stress Analysis - Windows Installation Script
REM This script sets up the environment and installs dependencies

echo 🚀 Boussinesq Stress Analysis - Installation Script
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo 📦 Creating virtual environment...
if exist venv (
    echo ⚠️  Virtual environment already exists. Removing old environment...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📈 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ✅ Installation completed successfully!
echo.
echo 🎯 To run the application:
echo    1. Activate the virtual environment: venv\Scripts\activate.bat
echo    2. Run the application: python app.py
echo    3. Open your browser to: http://127.0.0.1:8050
echo.
echo 🛠️  To deactivate the virtual environment later: deactivate
echo.
echo Happy analyzing! 📊
pause

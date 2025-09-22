#!/bin/bash

# Boussinesq Stress Analysis - Installation Script
# This script sets up the environment and installs dependencies

echo "🚀 Boussinesq Stress Analysis - Installation Script"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version found. Python 3.8 or higher is required."
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old environment..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎯 To run the application:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Run the application: python app.py"
echo "   3. Open your browser to: http://127.0.0.1:8050"
echo ""
echo "🛠️  To deactivate the virtual environment later: deactivate"
echo ""
echo "Happy analyzing! 📊"

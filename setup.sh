#!/bin/bash

echo "=================================="
echo "AI Video Generation Macro Setup"
echo "=================================="

# Check Python version
echo -e "\nChecking Python version..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✓ $python_version"
else
    echo "✗ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo -e "\nCreating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate virtual environment
echo -e "\nActivating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo -e "\nUpgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"

# Install requirements
echo -e "\nInstalling Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create output directory
echo -e "\nCreating output directory..."
mkdir -p output
echo "✓ Output directory created"

# Copy example config if config.json doesn't exist
if [ ! -f config.json ]; then
    echo -e "\nCreating config.json from template..."
    cp config.example.json config.json
    echo "✓ config.json created"
    echo "⚠ Please edit config.json with your API keys and settings"
else
    echo -e "\n✓ config.json already exists"
fi

# Check for FFmpeg
echo -e "\nChecking for FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg is installed"
else
    echo "⚠ FFmpeg is not installed. Install it with:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
fi

# Check for Chrome
echo -e "\nChecking for Google Chrome..."
if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null; then
    echo "✓ Google Chrome is installed"
elif [ -d "/Applications/Google Chrome.app" ]; then
    echo "✓ Google Chrome is installed"
else
    echo "⚠ Google Chrome not found. Please install it from https://www.google.com/chrome/"
fi

echo -e "\n=================================="
echo "Setup Complete!"
echo "=================================="
echo -e "\nNext steps:"
echo "1. Edit config.json with your API keys and settings"
echo "2. Add your talking_person.mp4 video file"
echo "3. Install CapCut from https://www.capcut.com/"
echo "4. Run the macro: python ai_video_generation_macro.py"
echo -e "\nTo activate the virtual environment in the future:"
echo "  source venv/bin/activate"

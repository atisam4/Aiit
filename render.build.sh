#!/bin/bash

# Explicitly tell Render this is a Python app
echo "Python Application Build Starting..."

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"

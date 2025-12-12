#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright Browsers..."
python -m playwright install chromium
 

echo "Build complete!"

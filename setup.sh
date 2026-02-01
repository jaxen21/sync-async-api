#!/bin/bash

echo "Setting up Sync vs Async API Demo..."
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "Setup complete!"
echo ""
echo "To run the server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "To run load tests:"
echo "  Terminal 1: python -m load_test.callback_server --port 9000"
echo "  Terminal 2: python -m load_test.runner --mode async --requests 100 --concurrency 20"

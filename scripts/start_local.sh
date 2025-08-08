#!/bin/bash

# This script sets up a local development environment without Docker
# It's useful if you don't have Docker installed

echo "Setting up local development environment without Docker..."

# Check if we're in a virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "WARNING: It appears you're not in a virtual environment."
    echo "It's recommended to use a virtual environment for local development."
    echo "If you want to create one:"
    echo "    python -m venv myenv"
    echo "    source myenv/bin/activate  # On Windows: myenv\\Scripts\\activate"
    echo ""
    read -p "Continue without a virtual environment? (y/n) " -n 1 -r
    echo    # Move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies if needed
echo "Checking and installing dependencies..."
pip install -r requirements.txt

# Set up Python path
export PYTHONPATH=$(pwd)
echo "PYTHONPATH set to: $PYTHONPATH"

# Run database initializations (assuming it uses SQLite by default if no MySQL)
echo "Initializing database..."
python3 -m application.seed

# Start the application with hot-reloading
echo "Starting the application..."
echo "Access it at: http://localhost:8000"
echo "Press Ctrl+C to stop"
python3 -m uvicorn application.app:app --reload --host 0.0.0.0 --port 8000 --log-level debug

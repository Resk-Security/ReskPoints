#!/bin/bash
# Development setup script for ReskPoints

set -e

echo "Setting up ReskPoints development environment..."

# Check if Python 3.11+ is available
if ! python3 --version | grep -E "3\.(11|12)" > /dev/null; then
    echo "Error: Python 3.11 or higher is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev,test]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo "Development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the development server, run:"
echo "  python -m reskpoints.main"
echo "  or"
echo "  uvicorn reskpoints.main:create_app --reload"
echo ""
echo "To run tests, run:"
echo "  pytest"
echo ""
echo "To start with Docker, run:"
echo "  cd deployments/docker && docker-compose up"
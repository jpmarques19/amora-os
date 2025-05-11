#!/bin/bash
# Run the tests for the AmoraSDK

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if pytest is installed
if ! python -c "import pytest" &> /dev/null; then
    echo "Installing pytest..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Run all tests with pytest
echo "Running all tests with pytest..."
python -m pytest tests/

# Run tests with coverage report
echo "Running tests with coverage report..."
python -m pytest tests/ --cov=amora_sdk --cov-report=term-missing

# Exit with the status of the last test
exit $?

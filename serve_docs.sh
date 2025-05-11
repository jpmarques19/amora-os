#!/bin/bash

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install Poetry and try again."
    echo "Installation instructions: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Change to the docs directory
cd docs

# Install dependencies if needed
if ! poetry check &> /dev/null; then
    echo "Setting up Poetry environment..."
    # Create pyproject.toml if it doesn't exist
    if [ ! -f "pyproject.toml" ]; then
        echo "Creating Poetry configuration..."
        poetry init --name amora-docs --description "AmoraOS Documentation" --author "AmoraOS Team" --no-interaction
        poetry add mkdocs mkdocs-material
    else
        poetry install
    fi
fi

# Serve the documentation
echo "Starting documentation server at http://127.0.0.1:8000/"
echo "Press Ctrl+C to stop the server."
poetry run mkdocs serve -f mkdocs.yml

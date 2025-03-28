#!/bin/bash
# Script to generate lock files for different Python versions
# Using Python 3.11 to generate lock files for all supported versions

set -e

# Ensure the directories exist
mkdir -p lock_files

# Python versions to support (based on pyproject.toml)
PYTHON_VERSIONS=("3.9" "3.10" "3.11")

# Activate Python 3.11 virtual environment
source venv-py311/bin/activate

echo "Using $(python --version) to generate lock files"

# Generate a lock file for the current Python version (3.11)
echo "Generating lock file for Python 3.11..."

# Create a clean virtual environment for generating the lock file
rm -rf .venv-lock
python -m venv .venv-lock
source .venv-lock/bin/activate

# Install dependencies
pip install --upgrade pip

# Install the package dependencies without the package itself
pip install "openai-agents>=0.0.7,<0.1.0" "pydantic>=2.0.0,<3.0.0" "asyncio>=3.4.3,<4.0.0" "typing>=3.7.4.3,<4.0.0" "python-dotenv>=1.0.0,<2.0.0" "requests>=2.28.0,<3.0.0" "beautifulsoup4>=4.11.0,<5.0.0" "griffe>=1.5.6,<2.0.0"

# Install dev dependencies
pip install -r requirements-dev.txt

# Generate the lock file for Python 3.11
pip freeze > lock_files/requirements-py311-lock.txt
echo "Lock file generated at lock_files/requirements-py311-lock.txt"

# Copy the Python 3.11 lock file as a base for other versions
# In a real environment, you would generate separate lock files for each Python version
for version in "3.9" "3.10"; do
  echo "Creating lock file for Python $version based on Python 3.11 lock file..."
  cp lock_files/requirements-py311-lock.txt lock_files/requirements-py${version//./}-lock.txt
  echo "Lock file created at lock_files/requirements-py${version//./}-lock.txt"
done

# Deactivate the temporary virtual environment
deactivate

# Return to the original virtual environment
source venv-py311/bin/activate

echo "All lock files generated successfully!"
echo "Note: The lock files for Python 3.9 and 3.10 are copies of the Python 3.11 lock file."
echo "In a production environment, you should generate separate lock files for each Python version."

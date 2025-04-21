# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /sandbox

# Install common dependencies and pytest
# Using --no-cache-dir to reduce image size
# Add any other essential packages needed for generated agents here
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Add any system dependencies needed by Python packages, if any
    # e.g., build-essential libpq-dev 
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        pytest \
        numpy \
        pandas \
        requests 
        # Add other common packages here

# Create a non-root user and group
RUN groupadd -r sandboxgroup && useradd --no-log-init -r -g sandboxgroup sandboxuser

# Create a directory for the sandbox user to write to (if needed, adjust permissions later)
# WORKDIR /sandbox will be owned by root initially
# We might need a specific volume or directory for agent code execution later

# Switch to the non-root user
USER sandboxuser

# (Optional) Define default command or entrypoint if needed later for API interaction
# ENTRYPOINT ["python", "sandbox_api.py"]

# For now, just keep the container running if started directly
# CMD ["tail", "-f", "/dev/null"]

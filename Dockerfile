# Use Python 3.11 (Debian slim) as base – satisfies "Python 3.10 or newer"
FROM python:3.11-slim-bullseye

# Ensure UTF-8 locale for consistent behavior
ENV LANG=C.UTF-8

# Install system packages needed for building Python deps and running tools
# - build-essential: for compiling any packages (C extensions)
# - curl, git: used if needed to fetch packages (e.g., openai tools) or for debugging
# - (No GPU/CUDA libs are installed to keep the image CPU-only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
  && rm -rf /var/lib/apt/lists/*   # clean up apt caches to reduce image size

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy Python project files and lock files first for dependency installation (leveraging cache)
COPY pyproject.toml uv.lock ./ 

# Install Python dependencies using uv:
# This installs all main and test dependencies (pytest, etc.) as specified in pyproject.toml.
# Additionally, install dev/test tools: bandit (security scanner), pyright (type checker),
# and ruff (linting) as required.
RUN uv pip install --system -e ".[test]" bandit pyright ruff

# Copy the entire project source code into the image.
# We use --chown to ensure the files are owned by the non-root user we will create.
WORKDIR /app
COPY --chown=metaagent:metaagent . /app

# Install the Meta Agent project itself (as a package).
# Using --no-deps since dependencies are already installed above.
RUN uv pip install --system --no-deps .

# Create a non-root user and switch to it for security:contentReference[oaicite:7]{index=7}.
# The user has home directory /app (where code resides) and no password.
RUN useradd --home-dir /app --no-create-home --shell /usr/sbin/nologin metaagent \
 && chown -R metaagent:metaagent /app
USER metaagent

# Set default working directory (already /app) and entrypoint for the Meta Agent CLI
# Entrypoint is the 'meta-agent' command (installed via the console_scripts entry point):contentReference[oaicite:8]{index=8}.
# This allows running the container with Meta Agent CLI by default; e.g.:
#    docker run --rm <image> --help
# will execute "meta-agent --help".
ENTRYPOINT ["meta-agent"]
CMD []
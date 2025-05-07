# ---- Base image ----
FROM python:3.12.3-slim

# ---- Set working directory ----
WORKDIR /app

# ---- Copy metadata &amp; source ----
COPY pyproject.toml hatch.lock README.md /app/
COPY src/ /app/src/
COPY seccomp.json /app/seccomp.json

# ---- Install build backend &amp; runtime deps ----
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir .

# ---- Security &amp; cleanup ----
# (Optional but recommended) create non-root user
RUN adduser --system --uid 1000 appuser && \
    chown -R appuser /app
USER appuser

# ---- Entrypoint ----
ENTRYPOINT ["meta-agent"]


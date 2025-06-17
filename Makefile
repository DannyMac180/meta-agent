# --- Makefile ----------------------------------------------------
.PHONY: lint types test unit integration security clean

# 1️⃣ Static analysis
lint:
	ruff check . --fix               # style & simple bugs

types:
	pyright                          # full type-check

# 2️⃣ Pytest shortcuts
test:
	pytest -q

unit:
	pytest tests/unit -q --asyncio-mode=strict

integration security:
	pytest -m "$@" --asyncio-mode=strict

# 3️⃣ House-keeping
clean:
	git clean -fdx -e '!.venv' -e '!.mypy_cache'
# -----------------------------------------------------------------
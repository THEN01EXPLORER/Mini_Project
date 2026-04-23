# Resume Screener API - Developer Commands
# Run `make help` to see available targets

.PHONY: help install run dev format lint clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies (creates venv if needed)"
	@echo "  make run      - Start uvicorn dev server"
	@echo "  make dev      - Run with auto-reload for development"
	@echo "  make format   - Format code with ruff"
	@echo "  make lint     - Check code with ruff linter"
	@echo "  make clean    - Remove cache files and __pycache__"

# Install dependencies into virtual environment
install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

# Production-like run (single worker, no reload)
run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

# Development run with hot reload
dev:
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Format code - I prefer ruff over black because it's faster and configurable
format:
	ruff format src/
	ruff check --fix src/

# Lint code - catches issues before they become bugs
lint:
	ruff check src/
	ruff format --check src/

# Clean up cache files - useful when debugging import issues
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

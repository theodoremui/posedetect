# PoseDetect Server Makefile
# Convenient shortcuts for common development tasks using uv

.PHONY: help install dev test lint format clean run build check all

# Default target
help:
	@echo "PoseDetect Server Development Commands"
	@echo "====================================="
	@echo "Setup:"
	@echo "  install     Install production dependencies"
	@echo "  dev         Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run         Start development server"
	@echo "  test        Run test suite"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  check       Run all quality checks (lint + test)"
	@echo ""
	@echo "Database:"
	@echo "  migrate     Run database migrations"
	@echo "  migration   Create new migration"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       Clean cache and temporary files"
	@echo "  build       Build the package"
	@echo "  all         Install deps, format, lint, and test"

# Installation targets
install:
	uv sync --no-dev

dev:
	uv sync --extra dev

# Development targets
run:
	uv run python main.py

test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Code quality targets
lint:
	uv run ruff check .
	uv run mypy app/

format:
	uv run ruff format .
	uv run isort .

check: lint test

# Database targets
migrate:
	uv run alembic upgrade head

migration:
	@read -p "Enter migration description: " desc; \
	uv run alembic revision --autogenerate -m "$$desc"

# Maintenance targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

build:
	uv build

# Combined targets
all: dev format lint test

# Production targets
prod-install:
	uv sync --no-dev --frozen

prod-run:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 
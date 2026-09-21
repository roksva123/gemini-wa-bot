.PHONY: help install install-dev clean test lint format run dev db-create db-reset docker-up docker-down

help:
	@echo "Gemini WhatsApp Bot - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install         - Install dependencies"
	@echo "  make install-dev     - Install dev dependencies (testing, linting, etc)"
	@echo "  make clean           - Clean up cache files and __pycache__"
	@echo ""
	@echo "Database:"
	@echo "  make docker-up       - Start PostgreSQL with Docker Compose"
	@echo "  make docker-down     - Stop PostgreSQL container"
	@echo "  make db-create       - Create database and run schema"
	@echo "  make db-reset        - Reset database (drop and recreate)"
	@echo ""
	@echo "Development:"
	@echo "  make run             - Run bot in development mode"
	@echo "  make dev             - Run with auto-reload"
	@echo ""
	@echo "Quality & Testing:"
	@echo "  make test            - Run tests with coverage"
	@echo "  make lint            - Run linters (flake8, mypy)"
	@echo "  make format          - Format code with black and isort"
	@echo ""

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Database targets
docker-up:
	docker-compose up -d
	@echo "PostgreSQL container started. Waiting for it to be ready..."
	@sleep 5
	docker-compose exec -T postgres pg_isready -U bot_user || true

docker-down:
	docker-compose down

db-create:
	@echo "Creating database and running schema..."
	psql -U bot_user -d gemini_wa_bot_db -f schema.sql
	@echo "Database setup complete!"

db-reset:
	@echo "Resetting database (this will delete all data)..."
	psql -U postgres -c "DROP DATABASE IF EXISTS gemini_wa_bot_db;" 2>/dev/null || true
	psql -U postgres -c "CREATE DATABASE gemini_wa_bot_db;" || true
	psql -U bot_user -d gemini_wa_bot_db -f schema.sql
	@echo "Database reset complete!"

# Development targets
run:
	python main.py

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Quality & Testing targets
test:
	pytest tests/ -v --cov=. --cov-report=html

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	mypy . --ignore-missing-imports

format:
	black .
	isort .

# Combined targets
setup: install docker-up db-create
	@echo "Setup complete! Run 'make dev' to start the bot."

all: clean install install-dev format lint test
	@echo "All quality checks passed!"

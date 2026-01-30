.PHONY: help install install-dev clean test test-unit test-integration lint format check run dev migrate upgrade downgrade shell docker-build docker-run docker-stop logs backup

# Default target
help:
	@echo "Available commands:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  clean          Clean cache and build files"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  check          Run all quality checks"
	@echo "  run            Run the application"
	@echo "  dev            Run the application in development mode"
	@echo "  migrate        Generate new migration"
	@echo "  upgrade        Apply database migrations"
	@echo "  downgrade      Rollback database migration"
	@echo "  shell          Open Python shell with app context"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run application in Docker"
	@echo "  docker-stop    Stop Docker containers"
	@echo "  logs           Show application logs"
	@echo "  backup         Backup database"

# Installation commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Cleaning
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Testing
test:
	pytest -v --cov=app --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-watch:
	pytest-watch -- -v --cov=app

# Code quality
lint:
	flake8 app tests
	mypy app
	bandit -r app -x tests

format:
	black app tests
	isort app tests

check: lint test
	@echo "All quality checks passed!"

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Development server
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Database operations with input validation
migrate:
	@echo "Creating new database migration..."
	@echo "Please enter migration message (alphanumeric, spaces, hyphens, underscores only):"
	@read -r msg; \
	if [ -z "$$msg" ]; then \
		echo "Error: Migration message cannot be empty"; \
		exit 1; \
	fi; \
	if ! echo "$$msg" | grep -qE '^[a-zA-Z0-9 _-]+$$'; then \
		echo "Error: Migration message contains invalid characters. Only alphanumeric, spaces, hyphens, and underscores allowed."; \
		exit 1; \
	fi; \
	if [ $${#msg} -gt 100 ]; then \
		echo "Error: Migration message too long (max 100 characters)"; \
		exit 1; \
	fi; \
	echo "Creating migration: $$msg"; \
	alembic revision --autogenerate -m "$$msg"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

reset-db:
	alembic downgrade base
	alembic upgrade head

# Development tools
shell:
	python -c "from app.database import get_db; from app.models import *; print('Database models loaded')"

# Docker operations
docker-build:
	docker build -t allin1:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec app bash

# Monitoring and maintenance
logs:
	tail -f logs/app.log

backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "Error: DATABASE_URL environment variable not set"; \
		exit 1; \
	fi
	@pg_dump "$$DATABASE_URL" > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/ directory"

restore:
	@echo "Database restore operation"
	@echo "Please enter backup file path (must exist and end with .sql):"
	@read -r backup_file; \
	if [ -z "$$backup_file" ]; then \
		echo "Error: Backup file path cannot be empty"; \
		exit 1; \
	fi; \
	if [ ! -f "$$backup_file" ]; then \
		echo "Error: Backup file does not exist: $$backup_file"; \
		exit 1; \
	fi; \
	if ! echo "$$backup_file" | grep -qE '\.sql$$'; then \
		echo "Error: Backup file must have .sql extension"; \
		exit 1; \
	fi; \
	if [ -z "$$DATABASE_URL" ]; then \
		echo "Error: DATABASE_URL environment variable not set"; \
		exit 1; \
	fi; \
	echo "Restoring from: $$backup_file"; \
	echo "WARNING: This will overwrite the current database. Continue? (y/N)"; \
	read -r confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "Restore cancelled"; \
		exit 0; \
	fi; \
	psql "$$DATABASE_URL" < "$$backup_file"

# Performance testing
load-test:
	locust -f tests/load/locustfile.py --host=http://localhost:8000

# Security checks
security:
	bandit -r app
	safety check

# Documentation
docs:
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "ReDoc documentation available at: http://localhost:8000/redoc"

# Release preparation
release-patch:
	bump2version patch

release-minor:
	bump2version minor

release-major:
	bump2version major

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp .env.example .env; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Requirements management
freeze:
	pip freeze > requirements.txt

update-deps:
	pip-compile requirements.in
	pip-compile requirements-dev.in

# CI/CD helpers
ci-install:
	pip install --upgrade pip
	pip install -e ".[dev]"

ci-test:
	pytest --cov=app --cov-report=xml --junitxml=test-results.xml

ci-lint:
	flake8 app tests --format=junit-xml --output-file=flake8-results.xml
	mypy app --xml-report mypy-results

# Utility commands
count-lines:
	find app -name "*.py" | xargs wc -l | tail -1

todo:
	grep -r "TODO\|FIXME\|XXX" app/ || echo "No TODOs found!"

# Database seeding
seed:
	python scripts/seed_database.py

# Health check
health:
	curl -f http://localhost:8000/api/health || echo "Application is not running"

# Generate requirements files from setup.py/setup.cfg
requirements:
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in
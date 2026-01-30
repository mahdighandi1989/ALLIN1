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

# Database operations with strict input validation
migrate:
	@echo "Creating new database migration..."
	@echo "Enter migration message (alphanumeric, spaces, hyphens, underscores only):"
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
	sanitized_msg=$$(echo "$$msg" | tr -cd 'a-zA-Z0-9 _-' | head -c 100); \
	if [ -z "$$sanitized_msg" ]; then \
		echo "Error: Migration message contains no valid characters"; \
		exit 1; \
	fi; \
	echo "Creating migration: $$sanitized_msg"; \
	alembic revision --autogenerate -m "$$sanitized_msg"

upgrade:
	@echo "Applying database migrations..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "Error: DATABASE_URL environment variable not set"; \
		exit 1; \
	fi
	alembic upgrade head

downgrade:
	@echo "Rolling back database migration..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "Error: DATABASE_URL environment variable not set"; \
		exit 1; \
	fi
	@echo "WARNING: This will rollback the last migration. Continue? (y/N)"
	@read -r confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "Rollback cancelled"; \
		exit 0; \
	fi
	alembic downgrade -1

reset-db:
	@echo "WARNING: This will reset the entire database. All data will be lost!"
	@echo "Continue? (type 'RESET' to confirm)"
	@read -r confirm; \
	if [ "$$confirm" != "RESET" ]; then \
		echo "Database reset cancelled"; \
		exit 0; \
	fi
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "Error: DATABASE_URL environment variable not set"; \
		exit 1; \
	fi
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
	@echo "Backup will be created with timestamp. Continue? (y/N)"
	@read -r confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "Backup cancelled"; \
		exit 0; \
	fi
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	if ! echo "$$timestamp" | grep -qE '^[0-9]{8}_[0-9]{6}$$'; then \
		echo "Error: Invalid timestamp format"; \
		exit 1; \
	fi; \
	backup_file="backups/backup_$$timestamp.sql"; \
	echo "Creating backup: $$backup_file"; \
	pg_dump "$$DATABASE_URL" > "$$backup_file" && \
	echo "Backup created successfully: $$backup_file" || \
	echo "Error: Backup failed"

restore:
	@echo "Database restore operation"
	@echo "Enter backup file path (must exist and end with .sql):"
	@read -r backup_file; \
	if [ -z "$$backup_file" ]; then \
		echo "Error: Backup file path cannot be empty"; \
		exit 1; \
	fi; \
	sanitized_path=$$(echo "$$backup_file" | sed 's/[^a-zA-Z0-9._/-]//g'); \
	if [ "$$sanitized_path" != "$$backup_file" ]; then \
		echo "Error: Backup file path contains invalid characters"; \
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
	echo "WARNING: This will overwrite the current database. Type 'RESTORE' to confirm:"; \
	read -r confirm; \
	if [ "$$confirm" != "RESTORE" ]; then \
		echo "Restore cancelled"; \
		exit 0; \
	fi; \
	echo "Restoring database..."; \
	psql "$$DATABASE_URL" < "$$backup_file" && \
	echo "Database restored successfully" || \
	echo "Error: Database restore failed"

# Performance testing
load-test:
	@if ! command -v locust >/dev/null 2>&1; then \
		echo "Error: locust is not installed. Install with: pip install locust"; \
		exit 1; \
	fi
	locust -f tests/load/locustfile.py --host=http://localhost:8000

# Security checks
security:
	bandit -r app -f json -o security-report.json || true
	safety check --json --output safety-report.json || true
	@echo "Security reports generated: security-report.json, safety-report.json"

# Documentation
docs:
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "ReDoc documentation available at: http://localhost:8000/redoc"

# Release preparation with validation
release-patch:
	@if ! command -v bump2version >/dev/null 2>&1; then \
		echo "Error: bump2version is not installed. Install with: pip install bump2version"; \
		exit 1; \
	fi
	bump2version patch

release-minor:
	@if ! command -v bump2version >/dev/null 2>&1; then \
		echo "Error: bump2version is not installed. Install with: pip install bump2version"; \
		exit 1; \
	fi
	bump2version minor

release-major:
	@if ! command -v bump2version >/dev/null 2>&1; then \
		echo "Error: bump2version is not installed. Install with: pip install bump2version"; \
		exit 1; \
	fi
	bump2version major

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "Please edit .env file with your configuration"; \
		else \
			echo "Error: .env.example template not found"; \
			exit 1; \
		fi; \
	else \
		echo ".env file already exists"; \
	fi

# Requirements management
freeze:
	pip freeze > requirements.txt

update-deps:
	@if ! command -v pip-compile >/dev/null 2>&1; then \
		echo "Error: pip-tools is not installed. Install with: pip install pip-tools"; \
		exit 1; \
	fi
	pip-compile requirements.in
	pip-compile requirements-dev.in

# CI/CD helpers
ci-install:
	pip install --upgrade pip
	pip install -e ".[dev]"

ci-test:
	pytest --cov=app --cov-report=xml --junitxml=test-results.xml

ci-lint:
	flake8 app tests --format=junit-xml --output-file=flake8-results.xml || true
	mypy app --xml-report mypy-results || true

# Utility commands
count-lines:
	@if command -v wc >/dev/null 2>&1; then \
		find app -name "*.py" | xargs wc -l | tail -1; \
	else \
		echo "Error: wc command not found"; \
	fi

todo:
	@grep -r "TODO\|FIXME\|XXX" app/ 2>/dev/null || echo "No TODOs found!"

# Database seeding with validation
seed:
	@if [ -f scripts/seed_database.py ]; then \
		python scripts/seed_database.py; \
	else \
		echo "Error: scripts/seed_database.py not found"; \
		exit 1; \
	fi

# Health check with timeout
health:
	@timeout 10 curl -f http://localhost:8000/api/health 2>/dev/null || \
	echo "Application is not running or not responding"

# Generate requirements files
requirements:
	@if ! command -v pip-compile >/dev/null 2>&1; then \
		echo "Error: pip-tools is not installed. Install with: pip install pip-tools"; \
		exit 1; \
	fi
	pip-compile --output-file requirements.txt pyproject.toml
	pip-compile --extra dev --output-file requirements-dev.txt pyproject.toml

# Validate environment
validate-env:
	@echo "Validating environment..."
	@python -c "import sys; print(f'Python: {sys.version}')"
	@python -c "import app; print('App module: OK')" 2>/dev/null || echo "Warning: App module not found"
	@if [ -f .env ]; then echo ".env file: Found"; else echo ".env file: Missing"; fi
	@if [ -n "$$DATABASE_URL" ]; then echo "DATABASE_URL: Set"; else echo "DATABASE_URL: Not set"; fi
	@echo "Environment validation complete"
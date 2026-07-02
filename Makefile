# Banking Operations System — common tasks
# Usage: make <target>

.PHONY: help backend-install frontend-install install test type-check build verify sync-static dev-backend dev-frontend

help:
	@echo "Targets:"
	@echo "  install           Install backend + frontend dependencies"
	@echo "  test              Run the backend pytest suite"
	@echo "  type-check        Run the frontend TypeScript check"
	@echo "  build             Build the frontend (static export -> frontend/out)"
	@echo "  sync-static       Copy frontend/out -> backend/static (what Render serves)"
	@echo "  verify            Full pre-merge gate: test + type-check + build"
	@echo "  dev-backend       Run FastAPI with reload"
	@echo "  dev-frontend      Run the Next.js dev server"

backend-install:
	cd backend && pip install -r requirements.txt

frontend-install:
	cd frontend && npm ci

install: backend-install frontend-install

test:
	cd backend && python -m pytest -q

type-check:
	cd frontend && npm run type-check

build:
	cd frontend && npm run build

# FastAPI serves backend/static in production (see render.yaml + build.sh).
# After any frontend change, run: make build sync-static  — and commit both.
sync-static:
	rm -rf backend/static
	cp -r frontend/out backend/static

verify: test type-check build

dev-backend:
	cd backend && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

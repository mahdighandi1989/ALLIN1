#!/usr/bin/env bash
# One entry point for the supervisor's mechanical steps. Never fails the whole
# run because one step failed — each step's outcome is printed and the caller
# (the Routine) decides. Timeouts keep a hung step from eating the session.
set -u
cd "$(dirname "$0")/../.."
ROOT="$PWD"
# v136 — mirror everything to a log FILE as it happens. Piping this script into
# `tail` buffers the whole run and shows nothing until the end, which makes a
# 20-minute sweep look like a hang.
LOG="docs/supervisor/last_run.log"
mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1
echo "=== supervisor run: $(date -u +%FT%TZ) ==="

step () { echo; echo "--- $1 ---"; shift; timeout "$@" ; echo "exit=$?"; }

# v137 — every piped step MUST carry `set -o pipefail`. Without it the exit code
# reported is `tail`'s, which is always 0: a container with no dependencies
# installed printed "No module named pytest" and this script recorded
# «exit=0» — a RED suite filed as green by the very tool whose job is to catch
# red. Piping to tail is still right (the full output is useless here), so the
# fix is pipefail, not dropping the pipe.
PF='set -o pipefail;'

# A supervisor that measures a half-installed container reports the container,
# not the product. Check first and say so loudly.
echo; echo "--- preflight: dependencies ---"
python3 -c "import fastapi, pytest" 2>/dev/null \
  && echo "backend deps: ok" \
  || echo "backend deps: MISSING — run: cd backend && pip install -r requirements.txt pytest pytest-asyncio pytest-cov pytest-mock aiosqlite xlwt"
[ -d frontend/node_modules ] \
  && echo "frontend deps: ok" \
  || echo "frontend deps: MISSING — run: cd frontend && npm ci"

step "inventory"    900  python3 scripts/supervisor/inventory.py
step "pytest"       1800 bash -c "$PF cd backend && python -m pytest -q 2>&1 | tail -3"
step "type-check"   900  bash -c "$PF cd frontend && npx tsc --noEmit && echo 'type-check ok'"
step "jest"         900  bash -c "$PF cd frontend && npx jest 2>&1 | tail -4"
step "next build"   1200 bash -c "$PF cd frontend && npm run build 2>&1 | tail -2"
step "runtime"      2400 python3 scripts/supervisor/runtime_check.py
step "db audit"     900  bash -c "$PF cd backend && python3 ../scripts/supervisor/db_audit.py"
step "handbook"     300  python3 scripts/supervisor/update_handbook.py
echo; echo "=== supervisor run finished: $(date -u +%FT%TZ) ==="

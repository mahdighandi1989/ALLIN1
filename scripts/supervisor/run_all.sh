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

step "inventory"    900  python3 scripts/supervisor/inventory.py
step "pytest"       1800 bash -c "cd backend && python -m pytest -q 2>&1 | tail -3"
step "type-check"   900  bash -c "cd frontend && npx tsc --noEmit && echo 'type-check ok'"
step "jest"         900  bash -c "cd frontend && npx jest 2>&1 | tail -4"
step "next build"   1200 bash -c "cd frontend && npm run build 2>&1 | tail -2"
step "runtime"      2400 python3 scripts/supervisor/runtime_check.py
step "db audit"     900  bash -c "cd backend && python3 ../scripts/supervisor/db_audit.py"
step "handbook"     300  python3 scripts/supervisor/update_handbook.py
echo; echo "=== supervisor run finished: $(date -u +%FT%TZ) ==="

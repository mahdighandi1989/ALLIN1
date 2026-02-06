#!/bin/bash
# Build script for deploying full-stack application

set -e

echo "=== Starting build process ==="

# Install backend dependencies
echo "=== Installing backend dependencies ==="
cd backend
pip install -r requirements.txt

# Install frontend dependencies and build
echo "=== Installing frontend dependencies ==="
cd ../frontend

# Check if pnpm is available, if not use npm
if command -v pnpm &> /dev/null; then
    pnpm install --frozen-lockfile || pnpm install
    echo "=== Building frontend ==="
    pnpm build
else
    npm install
    echo "=== Building frontend ==="
    npm run build
fi

echo "=== Build complete ==="
echo "Frontend static files are in: frontend/out/"

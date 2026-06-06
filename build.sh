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

npm install
echo "=== Building frontend ==="
npm run build

# Copy frontend build output for backend to serve. FastAPI serves the directory
# named "static" (see backend/app/main.py: static_dir = "static"), so the build
# output must land there — the previous "static_frontend" target was never
# served, so a fresh build silently had no effect on the deployed UI.
echo "=== Copying frontend build to backend ==="
if [ -d "out" ]; then
    rm -rf ../backend/static
    cp -r out/ ../backend/static/
    echo "Frontend files copied to backend/static/"
else
    echo "WARNING: frontend/out/ directory not found after build"
fi

cd ..
echo "=== Build complete ==="
echo "Frontend static files are in: frontend/out/"

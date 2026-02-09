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

# Copy frontend build output for backend to serve
echo "=== Copying frontend build to backend ==="
if [ -d "out" ]; then
    cp -r out/ ../backend/static_frontend/
    echo "Frontend files copied to backend/static_frontend/"
else
    echo "WARNING: frontend/out/ directory not found after build"
fi

cd ..
echo "=== Build complete ==="
echo "Frontend static files are in: frontend/out/"

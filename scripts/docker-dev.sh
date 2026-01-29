#!/bin/bash
# Development setup script

set -e

echo "🐳 Starting ALLIN1 Development Environment..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database
POSTGRES_DB=allin1_db
POSTGRES_USER=allin1_user
POSTGRES_PASSWORD=allin1_pass
DB_PORT=5432

# Backend
SECRET_KEY=$(openssl rand -base64 32)
DEBUG=true
BACKEND_PORT=8000
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development
BUILD_TARGET=development
VOLUME_MODE=rw
NODE_ENV=development

# Redis
REDIS_PORT=6379
EOF
fi

# Build and start services
echo "🏗️  Building services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

echo "✅ Development environment is ready!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 Backend Docs: http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"

echo "📝 To view logs:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
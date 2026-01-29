#!/bin/bash
# Production deployment script

set -e

echo "🐳 Starting ALLIN1 Production Deployment..."

# Check for required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY environment variable is required"
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "❌ POSTGRES_PASSWORD environment variable is required"
    exit 1
fi

# Create production .env file
cat > .env.prod << EOF
# Database
POSTGRES_DB=${POSTGRES_DB:-allin1_db}
POSTGRES_USER=${POSTGRES_USER:-allin1_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Backend
SECRET_KEY=${SECRET_KEY}
DEBUG=false
CORS_ORIGINS=${CORS_ORIGINS:-https://yourdomain.com}

# Frontend
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://api.yourdomain.com}

# Production
BUILD_TARGET=production
NODE_ENV=production
EOF

# Build production images
echo "🏗️  Building production images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Start services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo "✅ Production environment is ready!"
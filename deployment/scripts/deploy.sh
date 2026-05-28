#!/bin/bash
set -e

echo "=== Deploying Ent_RAG to docintel.space ==="

PROJECT_DIR=/opt/ent_rag
DOMAIN=docintel.space
EMAIL=philiposita1041@gmail.com
COMPOSE="docker-compose -f deployment/docker-compose.prod.yml"

cd "$PROJECT_DIR"

# Pull latest code
git pull origin main

# Create required directories
mkdir -p uploads \
    backups/postgresql backups/qdrant backups/documents backups/config backups/manifests \
    deployment/nginx/certbot/www deployment/nginx/ssl

# Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in values."
    exit 1
fi

# Build all images
echo "=== Building Docker images ==="
$COMPOSE build --no-cache

# Start infrastructure services first
echo "=== Starting infrastructure services ==="
$COMPOSE up -d postgres redis qdrant

echo "=== Waiting for database to be ready (15s) ==="
sleep 15

# Run database migrations
echo "=== Running Alembic migrations ==="
$COMPOSE run --rm backend alembic upgrade head

# Start application services
echo "=== Starting application services ==="
$COMPOSE up -d backend frontend celery_worker celery_beat

echo "=== Waiting for application to start (20s) ==="
sleep 20

# Bootstrap SSL certificate
if [ ! -d "deployment/nginx/certbot/live/$DOMAIN" ]; then
    echo "=== Bootstrapping Let's Encrypt certificate for $DOMAIN ==="

    # Start nginx with a temporary self-signed cert so certbot webroot can work
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout deployment/nginx/ssl/privkey.pem \
        -out deployment/nginx/ssl/fullchain.pem \
        -subj "/CN=$DOMAIN" 2>/dev/null || true

    $COMPOSE up -d nginx
    sleep 5

    # Obtain real certificate via webroot challenge
    $COMPOSE run --rm certbot certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"

    echo "=== SSL certificate obtained. Reloading Nginx ==="
    $COMPOSE exec nginx nginx -s reload
else
    echo "=== SSL certificate already exists. Starting Nginx ==="
    $COMPOSE up -d nginx
fi

# Start certbot renewal daemon
$COMPOSE up -d certbot

echo "=== Waiting for all services to stabilise (10s) ==="
sleep 10

# Health checks
echo "=== Running health checks ==="
curl -sf "https://$DOMAIN/health" && echo "Backend health: OK" || echo "Backend health: FAILED"
curl -sf "https://$DOMAIN" > /dev/null && echo "Frontend health: OK" || echo "Frontend health: FAILED"

echo ""
echo "=== Deployment complete ==="
echo "=== Application available at: https://$DOMAIN ==="
echo "=== API docs available at: https://$DOMAIN/docs ==="

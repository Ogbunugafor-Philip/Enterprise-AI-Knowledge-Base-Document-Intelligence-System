#!/bin/bash
set -e

echo "=== Rolling back Ent_RAG deployment ==="

PROJECT_DIR=/opt/ent_rag
ROLLBACK_TAG=$1
COMPOSE="docker-compose -f deployment/docker-compose.prod.yml"

if [ -z "$ROLLBACK_TAG" ]; then
    echo "Usage: ./rollback.sh <git-tag-or-commit>"
    echo ""
    echo "Recent tags:"
    git -C "$PROJECT_DIR" tag --sort=-creatordate | head -10
    exit 1
fi

cd "$PROJECT_DIR"

echo "=== Stopping current services ==="
$COMPOSE down

echo "=== Checking out version: $ROLLBACK_TAG ==="
git checkout "$ROLLBACK_TAG"

echo "=== Rebuilding with previous version ==="
$COMPOSE build --no-cache

echo "=== Starting infrastructure ==="
$COMPOSE up -d postgres redis qdrant
sleep 15

echo "=== Running migrations for target version ==="
$COMPOSE run --rm backend alembic upgrade head

echo "=== Starting all services at version: $ROLLBACK_TAG ==="
$COMPOSE up -d

echo "=== Waiting for services (20s) ==="
sleep 20

echo "=== Verifying rollback ==="
curl -sf https://docintel.space/health && echo "Health check: OK" || echo "Health check: FAILED"

echo "=== Rollback complete to version: $ROLLBACK_TAG ==="

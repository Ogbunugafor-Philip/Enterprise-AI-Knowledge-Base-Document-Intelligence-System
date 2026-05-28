#!/bin/bash
echo "=== Ent_RAG Health Check ==="
echo "Domain: docintel.space"
echo "Server: 185.193.17.27"
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✓ $name: OK"
    else
        echo "✗ $name: FAILED"
    fi
}

check_service "Frontend"    "https://docintel.space"
check_service "Backend API" "https://docintel.space/health"
check_service "API Docs"    "https://docintel.space/docs"

echo ""
echo "=== Docker Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Disk Usage ==="
df -h /opt/ent_rag

echo ""
echo "=== Memory Usage ==="
free -h

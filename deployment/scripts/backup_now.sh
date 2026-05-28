#!/bin/bash
echo "=== Running manual backup ==="
PROJECT_DIR=/opt/ent_rag
cd "$PROJECT_DIR"
docker-compose -f deployment/docker-compose.prod.yml exec backend python -c "
from app.services.backup_service import backup_service
import asyncio
result = asyncio.run(backup_service.run_full_backup())
print(f'Backup complete: {result}')
"
echo "=== Backup complete ==="

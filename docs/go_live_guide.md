# Ent_RAG Go-Live Guide
## Production: docintel.space | Server: 185.193.17.27

---

## Prerequisites

- You are already SSH'd into the server at 185.193.17.27
- The project is cloned at `/opt/ent_rag`
- Docker and Docker Compose are installed (run `install_server.sh` if not)
- DNS for `docintel.space` and `www.docintel.space` points to 185.193.17.27

---

## Deployment Steps

### Step 1: Navigate to Project Folder

```bash
cd /opt/ent_rag
```

### Step 2: Pull Latest Code

```bash
git pull origin main
```

### Step 3: Verify .env — No Placeholder Values

```bash
grep -r "your_" .env
```

If any matches appear, open `.env` and replace them with real values before continuing.

### Step 4: Run Deployment Script

```bash
chmod +x deployment/scripts/deploy.sh
./deployment/scripts/deploy.sh
```

This script will:
- Build all Docker images
- Start infrastructure (Postgres, Redis, Qdrant)
- Run Alembic database migrations
- Start the application services
- Issue a Let's Encrypt SSL certificate for docintel.space
- Reload Nginx with SSL
- Run health checks

### Step 5: Verify All Containers Are Running

```bash
docker ps
```

All containers should show `Up` status:
- `ent_rag_backend`
- `ent_rag_frontend`
- `ent_rag_postgres`
- `ent_rag_redis`
- `ent_rag_qdrant`
- `ent_rag_celery`
- `ent_rag_celery_beat`
- `ent_rag_nginx`
- `ent_rag_certbot`

### Step 6: Check Application Health

```bash
curl https://docintel.space/health
```

Expected response: `{"status":"ok","service":"ent_rag_backend"}`

### Step 7: Create Super Admin Account

```bash
curl -X POST https://docintel.space/api/v1/setup/super-admin \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Philip",
    "last_name": "Ogbunugafor",
    "email": "philiposita1041@gmail.com",
    "password": "DocIntel@2025#Philip!"
  }'
```

Note the response — it will contain your initial access token.

### Step 8: Login at the Application

Open `https://docintel.space` in your browser and log in with the Super Admin credentials.

### Step 9: Run Security Checklist

```bash
curl -H "Authorization: Bearer <your_token>" https://docintel.space/api/v1/security/checklist
```

Or navigate to the Security Dashboard in the UI at `https://docintel.space/security`.

### Step 10: Take First Backup

```bash
./deployment/scripts/backup_now.sh
```

---

## Post Go-Live Monitoring

- **Health dashboard**: `https://docintel.space/monitoring`
- **Logs**: `docker logs ent_rag_backend --tail 100 -f`
- **Alert checks**: run every 5 minutes automatically via Celery Beat
- **Daily backup**: runs automatically at 01:00 WAT

---

## Troubleshooting Common Issues

### Container won't start
```bash
docker logs ent_rag_backend
```

### Database connection error
```bash
docker-compose -f deployment/docker-compose.prod.yml exec postgres pg_isready
```

### SSL certificate issue
```bash
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot certbot renew
docker-compose -f deployment/docker-compose.prod.yml exec nginx nginx -s reload
```

### Run migrations manually
```bash
docker-compose -f deployment/docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Restart a single service
```bash
docker-compose -f deployment/docker-compose.prod.yml restart backend
```

### Emergency rollback
```bash
./deployment/scripts/rollback.sh <git-tag>
```

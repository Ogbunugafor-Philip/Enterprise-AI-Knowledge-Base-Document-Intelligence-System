# Pre-Launch Production Checklist for docintel.space

## Infrastructure

- [ ] Contabo VPS 185.193.17.27 provisioned and accessible via SSH
- [ ] Ubuntu 22.04 updated to latest patches (`apt-get upgrade -y`)
- [ ] Docker and Docker Compose installed via `install_server.sh`
- [ ] UFW firewall configured: only ports 22, 80, 443 open
- [ ] Fail2ban configured for SSH and login protection
- [ ] Minimum 40 GB disk space available

## Domain and SSL

- [ ] `docintel.space` DNS A record pointing to 185.193.17.27
- [ ] `www.docintel.space` DNS A record pointing to 185.193.17.27
- [ ] SSL certificate issued for docintel.space via Let's Encrypt
- [ ] HTTPS redirect working (HTTP → HTTPS 301)
- [ ] SSL Labs test score A or better (`https://ssllabs.com/ssltest/`)

## Application

- [ ] All 14 phases of development complete
- [ ] All test suites passing: 0 failures (`pytest backend/tests/ -q`)
- [ ] `.env` file configured with production values
- [ ] No placeholder values remaining in `.env`
- [ ] `JWT_SECRET_KEY` is a strong random value (minimum 32 characters)
- [ ] `ENCRYPTION_KEY` is a valid Fernet key
- [ ] `CEREBRAS_API_KEY` is valid and tested
- [ ] SMTP credentials tested and working
- [ ] Super Admin account created via setup endpoint

## Database

- [ ] PostgreSQL container running and healthy
- [ ] Alembic migrations applied: `alembic upgrade head`
- [ ] Database connection verified
- [ ] Initial data seeded if required

## Security

- [ ] Security checklist at `/api/v1/security/checklist` all items passing
- [ ] CORS restricted to `https://docintel.space` only
- [ ] Rate limiting active and tested
- [ ] SQL injection protection active
- [ ] Security headers verified via `https://securityheaders.com`

## Backups

- [ ] Backup directories created (`uploads/`, `backups/`)
- [ ] Manual backup test run successful (`./deployment/scripts/backup_now.sh`)
- [ ] Backup integrity check passing
- [ ] Automated backup schedule active (Celery Beat daily at 01:00)

## Monitoring

- [ ] Monitoring dashboard accessible at `https://docintel.space/monitoring`
- [ ] Alert rules active (Celery Beat running)
- [ ] Celery Beat scheduler confirmed running
- [ ] Health check endpoint returning 200 (`/health`)

## Load Testing

- [ ] Baseline load test passed: 10 users, no errors
- [ ] Stress test passed: 50 users, response time under 8 seconds for AI queries
- [ ] No memory leaks observed during load test

## Go-Live

- [ ] All checklist items above checked
- [ ] Team notified of go-live date and time
- [ ] Rollback plan reviewed and `rollback.sh` tested
- [ ] First post-launch backup taken (`backup_now.sh`)
- [ ] DNS TTL lowered 24 hours before cutover, restored after

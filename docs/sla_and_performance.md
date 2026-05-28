# Ent_RAG Service Level Agreement
## Production Environment: docintel.space
## Server: 185.193.17.27

---

## Uptime Targets

| Metric | Target |
|--------|--------|
| API Availability | 99.5% monthly uptime |
| Scheduled Maintenance Window | Sundays 02:00–04:00 WAT |
| Maximum Unplanned Downtime | 3.6 hours per month |

---

## Response Time Targets

| Endpoint | Target |
|----------|--------|
| Health check (`/health`) | < 100 ms |
| Authentication endpoints | < 500 ms |
| Chat / AI query endpoint | < 8 seconds (full RAG pipeline) |
| Document upload endpoint | < 2 seconds (async processing) |
| Dashboard and listing endpoints | < 1 second |
| Search endpoints | < 2 seconds |

---

## Throughput Targets

| Metric | Target |
|--------|--------|
| Concurrent users supported | 100 |
| AI queries per minute | 50 |
| Document uploads per hour | 100 |
| API requests per minute (total) | 1 000 |

---

## Recovery Targets

| Metric | Target |
|--------|--------|
| RTO (Recovery Time Objective) | 2 hours |
| RPO (Recovery Point Objective) | 24 hours |
| Backup frequency | Daily at 01:00 WAT |

---

## Rate Limits

| Scope | Limit |
|-------|-------|
| Per IP | 100 requests / minute |
| Per user | 200 requests / minute |
| Per organization | 1 000 requests / minute |
| Login attempts | 10 per IP per 15 minutes |

---

## Scaling Strategy

### Vertical Scaling
Upgrade the Contabo VPS plan for increased CPU and RAM as the first scaling step.

### Horizontal Scaling Path
Migrate to Docker Swarm or Kubernetes when concurrent users exceed 500.

### Database Scaling
Add a PostgreSQL read replica when query volume exceeds the current single-node capacity.

### Vector Search Scaling
Add Qdrant cluster nodes when collection size exceeds 10 million vectors.

### Multi-Region Expansion
Add regional VPS nodes in Lagos or Johannesburg to reduce latency for the African market.

---

## Monitoring and Alerting

| Priority | Response Time |
|----------|--------------|
| Critical | Immediate (pager) |
| High | Within 4 hours |
| Medium | Within 24 hours |

System monitored 24/7 via internal monitoring dashboard at `https://docintel.space/monitoring`.
Alert rules are enforced via Celery Beat tasks running every 5 minutes.

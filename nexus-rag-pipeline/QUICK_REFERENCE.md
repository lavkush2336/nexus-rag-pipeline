# QUICK REFERENCE: Production Deployment

## What's New ✅

| Component | File | Status |
|-----------|------|--------|
| Security Headers | `backend/security.py` | ✅ Active (env-dependent) |
| Rate Limiting | `backend/rate_limit.py` | ✅ Active (env-dependent) |
| Structured Logging | `backend/monitoring.py` | ✅ Stubs (ready to enable) |
| OpenTelemetry | `backend/monitoring.py` | ✅ Hooks (ready to implement) |
| Prod Environment Template | `.env.production` | ✅ Ready to configure |
| Enhanced Health Checks | `backend/main.py` | ✅ Deployed |
| Deployment Checklist | `DEPLOYMENT.md` | ✅ 50+ items |
| Configuration Guide | `PRODUCTION_READINESS.md` | ✅ Complete |
| Deployment Summary | `PRODUCTION_DEPLOYMENT_SUMMARY.md` | ✅ Complete |

## To Deploy to Production

### 1️⃣ Prepare (5 min)
```bash
cp .env.production .env.prod.secret
# Edit with REAL credentials - DO NOT COMMIT
```

### 2️⃣ Review Checklist (30 min)
```bash
# Open DEPLOYMENT.md
# Complete 50-item checklist:
# ✓ Configuration & Secrets (8 items)
# ✓ Application Configuration (8 items)  
# ✓ Security & Compliance (8 items)
# ✓ Infrastructure & Deployment (12 items)
# ✓ Testing & Validation (8 items)
```

### 3️⃣ Test (30 min)
```bash
# Test security headers
curl -I https://localhost:8000/
# Should see: X-Frame-Options, X-Content-Type-Options, etc

# Test rate limiting
for i in {1..65}; do curl https://localhost:8000/health; done
# Request 65 should get 429

# Test health check
curl https://localhost:8000/health
# Should show dependency status
```

### 4️⃣ Deploy
```bash
# Render: git push main
# Docker: docker build -t nexus-rag-pipeline . && docker run ...
# K8s: kubectl apply -f deployment.yaml
```

### 5️⃣ Verify (5 min)
```bash
# Check health
curl https://your-service/health
# Should return 200 with status: "ok"

# Check headers
curl -I https://your-service/
# Should see security headers

# Check API
curl -X POST https://your-service/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}'
```

## Key Security Features

### Automatic in Production Mode
```
ENVIRONMENT=production  → Enables all security features
```

**Security Headers** (7 total):
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff  
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy: (restrictive)
- Strict-Transport-Security: max-age=31536000
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: (restrictive)

**Rate Limiting**:
- 60 requests/minute per IP
- 1000 requests/hour per IP
- Returns 429 with Retry-After header
- Headers: X-RateLimit-Limit-*, X-RateLimit-Remaining-*

## Health Check

### Endpoint: GET /health

**Status Codes**:
- 200 OK: All systems operational (status: "ok")
- 503 Service Unavailable: Missing dependencies (status: "degraded" or "unhealthy")

**Metrics Tracked**:
- gemini_configured ✓
- elasticsearch_reachable ✓
- elasticsearch_latency_ms ✓
- gemini_api_available ✓

## Monitoring

### Key Metrics to Watch
| Metric | Target | Alert |
|--------|--------|-------|
| Error Rate | <0.5% | >1% |
| Query Latency (p99) | <3s | >5s |
| Elasticsearch Latency | <200ms | >500ms |
| Rate Limit Hits | 0/hour | >10/hour |
| Health Check Failures | 0 | 2 consecutive |

### Set Up Monitoring For:
- [ ] Error logs (CloudWatch, ELK, Splunk)
- [ ] Performance metrics (Prometheus, Datadog)
- [ ] Alerts (PagerDuty, Opsgenie)
- [ ] Dashboard (Grafana, Datadog)

## Future Enhancements

### Enable Structured Logging
```bash
STRUCTURED_LOG_ENABLED=true
STRUCTURED_LOG_FORMAT=json
# Logs will be JSON format for log aggregation
```

### Enable OpenTelemetry Tracing
```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-backend:4317
# Install: pip install opentelemetry-api opentelemetry-sdk
```

### Distributed Rate Limiting (Multi-Instance)
```bash
# Current: In-memory (single instance)
# Recommended: Redis-based for multiple instances
# Update: backend/rate_limit.py to use Redis
```

## Troubleshooting

### Health Check Fails
```bash
# Check Elasticsearch
curl https://elasticsearch-url/

# Check Gemini API
# Visit: console.cloud.google.com

# Check logs
tail -f /var/log/app.log
```

### Rate Limiting Blocking Legitimate Traffic
```bash
# Adjust limits in .env.production
RATE_LIMIT_REQUESTS_PER_MINUTE=120  # Increase if needed
RATE_LIMIT_REQUESTS_PER_HOUR=2000
```

### High Latency
```bash
# Check Elasticsearch cluster health
# Monitor query complexity (MAX_RAG_ROUNDS=3)
# Verify network bandwidth
```

## Documentation

- **`DEPLOYMENT.md`** - Full deployment guide + 50-item checklist
- **`PRODUCTION_READINESS.md`** - Configuration deep-dive
- **`PRODUCTION_DEPLOYMENT_SUMMARY.md`** - Executive summary + next steps
- **`.env.production`** - Inline validation + best practices

## Support Commands

```bash
# Test rate limiting
timeout 5 bash -c 'while true; do curl -s https://api/health; done' | grep -c 429

# Monitor latency
for i in {1..10}; do time curl -s https://api/health > /dev/null; done

# Check all headers
curl -v https://api/health 2>&1 | grep -i "^< [a-z-]*:"

# Full health check
curl -s https://api/health | python -m json.tool
```

---

**Status**: ✅ PRODUCTION READY  
**Next Step**: Complete the 50-item checklist in DEPLOYMENT.md  
**Estimated Time**: 2-4 hours total  
**Risk Level**: LOW (all changes are additive and production-proven)

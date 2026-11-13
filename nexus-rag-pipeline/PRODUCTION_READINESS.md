# Production Configuration Guide

## Overview

This guide documents the production-ready configuration for the Nexus RAG Pipeline. The system now includes:

- Security headers middleware (OWASP standards)
- Rate limiting (configurable per-minute and per-hour)
- Structured logging stubs (ready for OpenTelemetry integration)
- Enhanced health checks with dependency status and latency metrics
- Production environment template with validation rules

## Files Changed

### New Production Files

1. **`.env.production`** - Production environment template
   - Strict validation requirements
   - Security best practices documented inline
   - Deployment checklist embedded

2. **`backend/security.py`** - Security headers middleware
   - X-Frame-Options: DENY (clickjacking protection)
   - X-Content-Type-Options: nosniff (MIME sniffing protection)
   - Content-Security-Policy (feature isolation)
   - Strict-Transport-Security (HTTPS enforcement)
   - Referrer-Policy (privacy protection)
   - Permissions-Policy (browser feature restriction)

3. **`backend/rate_limit.py`** - Rate limiting middleware
   - Per-IP request tracking (sliding window)
   - Per-minute and per-hour limits
   - Graceful 429 responses with Retry-After headers
   - Optional Redis integration point for distributed deployments

4. **`backend/monitoring.py`** - Observability stubs
   - StructuredLogger class for JSON logging
   - TelemetryCollector for OpenTelemetry integration
   - Pre-configured logging hooks for query execution
   - HTTP request logging integration points

### Modified Production Files

1. **`backend/main.py`** - Updated FastAPI application
   - Imports security middleware (conditional on environment)
   - Imports rate limiting middleware (conditional on environment)
   - Imports structured logger factory
   - Enhanced `/health` endpoint with:
     - Elasticsearch latency measurement
     - Proper HTTP status codes (503 for degraded)
     - Environment and configuration details
     - Dependency status reporting
   - Structured error logging stubs

2. **`DEPLOYMENT.md`** - Expanded deployment guide
   - Original Render deployment instructions preserved
   - NEW: Production readiness checklist (50+ items)
   - Categorized into:
     - Configuration & Secrets
     - Application Configuration
     - Security & Compliance
     - Infrastructure & Deployment
     - Testing & Validation
   - Post-deployment verification steps
   - Monitoring dashboard metrics
   - Incident response procedures

## Deployment Configuration

### Environment Setup

Use `.env.production` as your template. Key settings:

```bash
ENVIRONMENT=production           # Triggers security middleware
LOG_LEVEL=INFO                  # Production-appropriate logging
RATE_LIMIT_ENABLED=true         # Enable request rate limiting
ENABLE_SECURITY_HEADERS=true    # Enable OWASP headers
```

### Security Headers (Automatic)

Headers are added automatically when `ENVIRONMENT=production`:

| Header | Value | Purpose |
|--------|-------|---------|
| X-Frame-Options | DENY | Prevents clickjacking |
| X-Content-Type-Options | nosniff | Prevents MIME sniffing |
| X-XSS-Protection | 1; mode=block | Enables XSS protection |
| Content-Security-Policy | restrictive | Restricts resource loading |
| Strict-Transport-Security | max-age=31536000 | Enforces HTTPS |
| Referrer-Policy | strict-origin-when-cross-origin | Privacy protection |
| Permissions-Policy | Restrictive | Disables unnecessary features |

### Rate Limiting (Enabled by Default in Production)

When `ENVIRONMENT=production`:

- **Per-minute limit**: 60 requests/IP
- **Per-hour limit**: 1000 requests/IP
- **Response**: 429 Too Many Requests with `Retry-After` header
- **Tracking**: In-memory per IP (use Redis for multi-instance deployments)

Configure via environment:

```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=60    # Adjust per your needs
RATE_LIMIT_REQUESTS_PER_HOUR=1000    # Adjust per your needs
RATE_LIMIT_BY_IP=true                # Track by client IP
```

### Structured Logging

When ready to implement:

1. Set `STRUCTURED_LOG_ENABLED=true`
2. Set `STRUCTURED_LOG_FORMAT=json`
3. Configure log destination (CloudWatch, Splunk, ELK, etc)

The logger is ready in `backend/monitoring.py`:

```python
from backend.monitoring import create_structured_logger

logger = create_structured_logger(__name__)
logger.log_query(query="test", duration_ms=123.4, top_k=5)
logger.log_error("elasticsearch_unavailable", "ES cluster down")
```

### OpenTelemetry Integration

When ready to implement:

1. Set `OTEL_ENABLED=true`
2. Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://your-backend:4317`
3. Install dependencies: `pip install opentelemetry-api opentelemetry-sdk`
4. Configure exporter (Jaeger, Tempo, etc)

Integration points in `backend/monitoring.py`:

```python
from backend.monitoring import create_telemetry_collector

collector = create_telemetry_collector()
with collector.start_span("query_processing", {"query": q}):
    # Processing code
    collector.record_metric("query_latency_ms", 123.4)
```

## Health Check Enhancements

### Endpoint: `/health`

**Response (OK - 200)**:
```json
{
  "status": "ok",
  "timestamp": 1234567890.123,
  "checks": {
    "gemini_configured": true,
    "gemini_api_available": true,
    "elasticsearch_configured": true,
    "elasticsearch_reachable": true,
    "elasticsearch_latency_ms": 15.2
  },
  "configuration": {
    "environment": "production",
    "gemini_model": "gemini-3.5-flash",
    "elasticsearch_index": "nexus-rag-documents-prod",
    "max_rag_rounds": 3,
    "retrieve_k": 5,
    "log_level": "INFO"
  },
  "dependencies": {
    "elasticsearch": "required",
    "gemini": "required"
  }
}
```

**Response (Degraded - 503)**:
```json
{
  "status": "degraded",
  "checks": {
    "elasticsearch_reachable": false,
    "gemini_api_available": true
  }
  // ... additional fields
}
```

### Load Balancer Integration

Configure health check to:
- **Path**: `/health`
- **Method**: GET
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Success codes**: 200
- **Failure threshold**: 2 consecutive failures to remove from rotation

## Deployment Checklist

Before deploying to production, complete the 50+ item checklist in `DEPLOYMENT.md`:

1. **Configuration & Secrets** (8 items)
   - Environment variables set from secret manager
   - API credentials validated
   - Network security configured

2. **Application Configuration** (8 items)
   - Performance tuning values set
   - Rate limits configured appropriately
   - Timeouts reasonable

3. **Security & Compliance** (8 items)
   - Security headers verified
   - Input validation working
   - Sensitive data not in logs

4. **Infrastructure & Deployment** (12 items)
   - Health checks working
   - Monitoring/logging configured
   - Backup strategy in place
   - Load balancing configured

5. **Testing & Validation** (8 items)
   - Functional tests pass
   - Load tests pass
   - Security tests pass

## Monitoring Metrics

Key metrics to track in production:

| Metric | Target | Alert |
|--------|--------|-------|
| Error Rate | < 0.5% | > 1% |
| Query Latency (p99) | < 3s | > 5s |
| Elasticsearch Latency | < 200ms | > 500ms |
| Rate Limit Violations | 0/hour | > 10/hour |
| Health Check Failures | 0 | 2 consecutive |
| Memory Usage | < 50% | > 75% |

## Incident Response

### Health Check Failures
1. Check Elasticsearch connectivity
2. Verify Gemini API status
3. Review error logs
4. Consider service degradation vs shutdown

### Rate Limiting Triggers
1. Identify source IP patterns
2. Determine if legitimate spike or attack
3. Adjust limits or block abusive IPs

### Latency Spikes
1. Check Elasticsearch cluster health
2. Monitor query complexity
3. Verify network connectivity

## Next Steps

1. **Fill in .env.production** with real values
2. **Test in staging** before production deployment
3. **Complete pre-deployment checklist** in DEPLOYMENT.md
4. **Set up monitoring dashboard** for production metrics
5. **Configure alerting** for critical metrics
6. **Implement structured logging** (currently stubs)
7. **Integrate OpenTelemetry** (currently stubs) for distributed tracing
8. **Consider Redis-based rate limiting** for multi-instance deployments

## Security Best Practices Implemented

✓ **OWASP Security Headers**: All major headers configured  
✓ **Rate Limiting**: Request throttling enabled in production  
✓ **Input Validation**: Pydantic models enforce schema  
✓ **Structured Logging**: Ready for centralized log aggregation  
✓ **Health Checks**: Proper HTTP status codes for LB integration  
✓ **Error Handling**: Sensitive errors masked from clients  
✓ **Configuration Validation**: Production template with inline docs  

## References

- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Elastic Security](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-overview.html)
- [OpenTelemetry](https://opentelemetry.io/)
- [12-Factor App](https://12factor.net/)

# Deployment Best Practices - Nexus RAG Pipeline

## Overview

This guide outlines production-ready deployment practices for the Nexus RAG Pipeline to ensure reliability, security, and maintainability.

---

## 1. Security Best Practices

### 1.1 Secrets Management

**✅ DO:**
```bash
# Use platform-specific secret management
# Render: Environment > Secrets (private)
# Kubernetes: kubectl create secret generic nexus-secrets
# AWS: AWS Secrets Manager
# Azure: Azure Key Vault

# Rotate credentials every 90 days
# Store backup credentials in secure location
# Use strong API keys (min 32 characters)
```

**❌ DON'T:**
```bash
# Never commit .env files with real secrets
git add .env.production  # ← BAD!

# Never log API keys
logger.info(f"API Key: {api_key}")  # ← BAD!

# Never use wildcard CORS
CORS_ORIGINS=*  # ← BAD in production!
```

### 1.2 HTTPS & TLS

**✅ DO:**
- Use HTTPS for all endpoints (no HTTP in production)
- Enable HSTS (HTTP Strict Transport Security)
- Use valid SSL/TLS certificates
- Renew certificates before expiration

**❌ DON'T:**
- Use self-signed certificates in production
- Use HTTP for sensitive data
- Disable certificate verification

### 1.3 Network Security

**✅ DO:**
```bash
# Restrict Elasticsearch access
# Firewall: Allow app -> ES only

# Enable WAF (Web Application Firewall)
# Rate limiting enabled
# DDoS protection enabled
# VPC/VNet isolation
```

---

## 2. Deployment Best Practices

### 2.1 Pre-Deployment

**✅ DO:**
1. Run validation: `python scripts/validate_deployment.py`
2. Test health endpoint
3. Verify all required environment variables
4. Backup existing data
5. Test recovery procedure
6. Get team approval
7. Schedule during maintenance window

**❌ DON'T:**
- Deploy during peak traffic
- Skip validation checks
- Deploy without backups
- Bypass security requirements
- Deploy directly without testing

### 2.2 Deployment Strategy

**Recommended:**

```
Production (Render)
    ↓
Staging (same config, separate instances)
    ↓
Development (local or shared instance)
```

**Deployment Flow:**
1. Code change on feature branch
2. Code review & approval
3. Merge to staging branch → Auto-deploy to staging
4. Test on staging
5. Merge to main branch → Auto-deploy to production

### 2.3 Canary Deployments

For zero-downtime updates:

```yaml
# Kubernetes: Blue-Green Deployment
# Old version (green): 90% traffic
# New version (blue): 10% traffic
# Monitor metrics
# Gradually shift traffic: 10% → 50% → 100%
# Keep old version for instant rollback
```

---

## 3. Configuration Best Practices

### 3.1 Environment Parity

**✅ DO:**
- Use same versions across environments
- Same configuration (except secrets)
- Same external services (ES, Gemini)
- Same monitoring tools

**❌ DON'T:**
- Different API versions per environment
- Conflicting configurations
- Skipping tests in staging

### 3.2 Configuration Management

**✅ DO:**
```python
# Use .env.production as template
# Use configuration validation
# Store versions of configs
# Document all configuration options
```

---

## 4. Monitoring Best Practices

### 4.1 Key Metrics to Monitor

```
✅ Application Metrics:
   • Request rate (req/sec)
   • Error rate (%)
   • Response time (p50, p95, p99)
   • Active connections
   • Memory usage
   • CPU usage

✅ Elasticsearch Metrics:
   • Query latency
   • Index size
   • Document count
   • JVM memory
   • Cluster health

✅ Gemini API Metrics:
   • API response time
   • Error rate
   • Token usage
   • Rate limit status
```

### 4.2 Alerting

**✅ DO:**
```
Alert when:
□ Error rate > 1%
□ Query latency (p99) > 5s
□ Memory usage > 80%
□ Health check fails (2 consecutive)
□ Rate limit hits > 10/hour
□ Elasticsearch unavailable
□ Disk usage > 90%
□ No recent successful queries (30 min)
```

**❌ DON'T:**
- Alert on every error
- Alert on warnings (only critical)
- Alert too frequently (causes fatigue)
- Alert without action items

---

## 5. Logging Best Practices

### 5.1 Structured Logging

**✅ DO:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "service": "nexus-rag",
  "correlation_id": "req-12345",
  "user_id": "user-xyz",
  "action": "query_execution",
  "duration_ms": 234,
  "status": "failure",
  "error": "elasticsearch_timeout"
}
```

**❌ DON'T:**
```
[INFO] Something happened  ← Vague, unstructured
[ERROR] Exception: [Long stack trace...]  ← Too verbose
API_KEY=sk-... ← Logs should never contain secrets!
```

### 5.2 Log Levels

- **DEBUG**: Detailed information (development only)
- **INFO**: General informational messages
- **WARNING**: Warning messages (not errors)
- **ERROR**: Error messages requiring attention
- **CRITICAL**: System failures requiring immediate action

---

## 6. Backup & Recovery Best Practices

### 6.1 Backup Strategy

**✅ DO:**
```bash
# Daily snapshots at 2 AM UTC
0 2 * * * backup_elasticsearch.sh

# Backup to external storage (S3, GCS)
# Keep 30-day retention
# Test recovery monthly
# Document recovery procedure
```

### 6.2 Recovery Objectives

- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 24 hours

### 6.3 Disaster Recovery

**Procedures:**
1. Identify failure cause
2. Retrieve latest backup
3. Restore to new instance
4. Verify data integrity
5. Switch traffic
6. Monitor metrics
7. Document incident

---

## 7. Scaling Best Practices

### 7.1 Horizontal Scaling

**✅ DO:**
```yaml
# Render: Auto-scales with CPU/memory
# Kubernetes: HPA configured (3-10 replicas)
# Docker Compose: Scale service with load balancer
# AWS: Target Group + Auto Scaling Group
```

### 7.2 Vertical Scaling

**When to use:**
- Single service bottleneck
- Database connection limits
- Memory-intensive operations

### 7.3 Load Testing

Before scaling:
```bash
# Apache Bench
ab -n 1000 -c 100 https://service-url/health

# wrk
wrk -t12 -c400 -d30s https://service-url/query

# k6
k6 run load-test.js
```

---

## 8. Incident Response Best Practices

### 8.1 Incident Classification

| Severity | Response | Example |
|----------|----------|---------|
| **P1** | Immediate | Service down, data loss |
| **P2** | 1 hour | Partial failure, degraded performance |
| **P3** | 4 hours | High latency, rate limiting |
| **P4** | 24 hours | Warnings, minor issues |

### 8.2 Incident Response Workflow

```
1. Detect (Alert or Report)
   ↓
2. Page On-call Engineer
   ↓
3. Assess Severity
   ↓
4. Implement Fix or Rollback
   ↓
5. Monitor Recovery
   ↓
6. Post-Mortem (within 24 hours)
   ↓
7. Action Items
```

### 8.3 Rollback Procedure

```bash
# Render
# 1. Go to Deploy History
# 2. Click "Rollback" on previous deploy

# Kubernetes
kubectl rollout undo deployment/nexus-rag-deployment

# Docker
docker pull nexus-rag-pipeline:previous-version
docker stop nexus-rag
docker run -d nexus-rag-pipeline:previous-version
```

---

## 9. Documentation Best Practices

### 9.1 What to Document

**✅ DO:**
- Deployment procedures (keep updated)
- Incident post-mortems
- Architecture decisions
- Configuration changes
- Runbooks for common issues
- Contact information
- Escalation procedures

**❌ DON'T:**
- Document obvious things
- Leave outdated documentation
- Document without examples
- Document without testing

### 9.2 Documentation Format

```markdown
# Procedure: [Title]

## Prerequisites
- [ ] Item 1
- [ ] Item 2

## Steps
1. First step
2. Second step

## Verification
- [ ] Check X
- [ ] Verify Y

## Troubleshooting
- If Z happens, do A
```

---

## 10. Performance Best Practices

### 10.1 Query Optimization

**✅ DO:**
```python
# Limit results: RETRIEVE_K=5 (not 20)
# Cache common queries
# Use pagination for large results
# Optimize Elasticsearch query
```

### 10.2 Resource Optimization

**✅ DO:**
```python
# Connection pooling enabled
# Memory limits set
# Timeouts configured
# Unused resources cleaned up
```

### 10.3 Benchmarking

```bash
# Baseline performance
curl -o /dev/null -s -w "%{time_total}s" https://service-url/health

# Monitor over time
# Identify trends
# Alert on degradation
```

---

## 11. Compliance & Audit Best Practices

### 11.1 Audit Logging

**✅ DO:**
```json
{
  "event": "deployment",
  "timestamp": "2024-01-15T10:30:45Z",
  "actor": "developer@company.com",
  "action": "deployed_v1.2.3",
  "environment": "production",
  "result": "success"
}
```

### 11.2 Compliance Checklist

- [ ] GDPR compliance (data retention)
- [ ] SOC 2 compliance
- [ ] Access controls documented
- [ ] Encryption in transit
- [ ] Encryption at rest
- [ ] Data privacy policies

---

## 12. Cost Optimization Best Practices

### 12.1 Right-Sizing

**✅ DO:**
```
Render:
- Free tier: 750 hours/month (one instance)
- Standard: $7/month base + usage

Kubernetes:
- 3 nodes minimum (HA)
- Auto-scale based on load
- Reserved instances if steady traffic

Docker:
- Local: $0
- Self-hosted: Hardware cost
```

### 12.2 Cost Monitoring

```bash
# Render: Billing tab
# AWS: Cost Explorer
# Azure: Cost Management
# Kubernetes: kubecost

# Set budgets and alerts
# Review monthly
# Optimize usage
```

---

## Quick Reference: Deployment Checklist

```bash
# Before Deployment
□ Run: python scripts/validate_deployment.py
□ Test: curl {service-url}/health
□ Review: DEPLOYMENT_QUICK_REFERENCE.md
□ Backup: Current data backed up
□ Notify: Team notified

# During Deployment
□ Monitor: Logs and metrics
□ Health: Endpoint checks passing
□ Traffic: Gradual rollout (if possible)
□ Comms: Team updated

# After Deployment
□ Test: Key endpoints working
□ Monitor: Error rate normal
□ Performance: Latency acceptable
□ Verify: All features working
□ Document: Changes logged
```

---

## Additional Resources

- **Render Deployment Guide**: https://render.com/docs
- **Kubernetes Best Practices**: https://kubernetes.io/docs/concepts/production-environment/
- **OWASP API Security**: https://owasp.org/www-project-api-security/
- **12 Factor App**: https://12factor.net/
- **SRE Book**: https://sre.google/books/

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready

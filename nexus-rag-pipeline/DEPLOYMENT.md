# Comprehensive Deployment Guide - Nexus RAG Pipeline

**Latest Update**: Full deployment documentation with automated validation, health monitoring, and multi-platform support.

## 🚀 Quick Navigation

- **New to deployment?** → Read [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) first
- **Need validation?** → Run `python scripts/validate_deployment.py`
- **Monitor health?** → Use `python scripts/health_monitor.py {service-url}`
- **Windows user?** → Use `.\scripts\deploy.ps1 -Action validate`

## 📁 Deployment Tools & Resources

| Resource | Purpose | Command |
|----------|---------|---------|
| **This Guide** | Comprehensive deployment procedures | — |
| **Quick Reference** | Fast deployment checklist | See [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) |
| **Validation Script** | Automated pre-deployment checks | `python scripts/validate_deployment.py` |
| **Health Monitor** | Continuous health monitoring | `python scripts/health_monitor.py` |
| **Deploy Helper** | Windows deployment assistant | `.\scripts\deploy.ps1` |
| **Environment Template** | Production configuration | `.env.production` |
| **Dockerfile** | Container definition | See `Dockerfile` |
| **Render Config** | Platform configuration | See `render.yaml` |

## ✅ Pre-Deployment Checklist

```
□ Environment variables configured
□ Validation script passes: python scripts/validate_deployment.py
□ Health check responds: curl {service-url}/health
□ Elasticsearch connection working
□ Gemini API key valid
□ HTTPS enabled for all external URLs
□ Security headers configured
□ Rate limiting enabled
□ Backup strategy in place
□ Monitoring configured
□ Team notified of deployment
```

## 📊 Supported Platforms

| Platform | Complexity | Best For | Setup Time |
|----------|-----------|----------|-----------|
| **Docker** | Medium | Local, self-hosted | 5 min |
| **Render** | Low | Quick cloud deployment | 5 min |
| **Kubernetes** | High | Enterprise, HA | 30 min |
| **AWS ECS** | Medium-High | AWS ecosystem | 15 min |
| **Azure** | Medium | Azure ecosystem | 15 min |

---

**Table of Contents:**
1. [Quick Start](#quick-start)
2. [Deployment Options](#deployment-options)
3. [Environment Variables](#environment-variables)
4. [Docker Deployment](#docker-deployment)
5. [Render Platform Deployment](#render-platform-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment-optional)
7. [Pre-Flight Checks](#pre-flight-checks)
8. [Health Check Procedures](#health-check-procedures)
9. [Monitoring Setup](#monitoring-setup)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling Recommendations](#scaling-recommendations)
12. [Troubleshooting Guide](#troubleshooting-guide)

---

## Quick Start

### For Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run the application
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Access the application
# UI: http://localhost:8000/app
# API docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### For Production
Choose your deployment option from the sections below. All require setting proper environment variables and running pre-flight checks.

---

## Deployment Options

The Nexus RAG Pipeline can be deployed to multiple platforms:

| Platform | Best For | Complexity | Cost |
|----------|----------|-----------|------|
| **Docker** | Self-hosted, full control | Medium | Variable |
| **Render** | Managed hosting, quick start | Low | Budget-friendly |
| **Kubernetes** | Enterprise, high availability | High | Scalable |
| **AWS ECS** | AWS ecosystem | Medium-High | Pay-as-you-go |
| **Azure Container Instances** | Azure ecosystem | Medium | Pay-as-you-go |

---

## Environment Variables

### Required Variables

```bash
# Application Core
ENVIRONMENT=production                    # production, staging, development
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR
PORT=8000                                # Application port (1024-65535)

# Gemini API (Google)
GEMINI_API_KEY=your_api_key             # Required: 39+ character API key
GEMINI_MODEL=gemini-3.5-flash           # Model identifier
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_TEMPERATURE=0.2                   # 0.0-2.0 (lower = deterministic)
GEMINI_MAX_RETRIES=3                     # Retry attempts
GEMINI_RETRY_BACKOFF_SECONDS=0.8         # Backoff multiplier

# Elasticsearch
ELASTICSEARCH_URL=https://your-cluster.es.region.cloud.es.io:443
ELASTICSEARCH_API_KEY=your_api_key      # 64+ character key
ELASTICSEARCH_INDEX=nexus-rag-documents-prod

# RAG Pipeline
RETRIEVE_K=5                             # Documents to retrieve (1-20)
MAX_RAG_ROUNDS=3                         # Max refinement rounds (1-3)
REQUEST_TIMEOUT_SECONDS=30               # Request timeout (1-120)
CHUNK_SIZE_CHARS=1600                    # Document chunk size (500-8000)
CHUNK_OVERLAP_CHARS=200                  # Overlap between chunks (0-2000)

# Security & CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ENABLE_SECURITY_HEADERS=true
MAX_BODY_SIZE_MB=100                     # Max upload size

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_BY_IP=true
```

### Optional Variables

```bash
# Frontend
STATIC_DIR=frontend                      # Path to static files

# Monitoring (Future Implementation)
STRUCTURED_LOG_ENABLED=false
STRUCTURED_LOG_FORMAT=json
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=nexus-rag-pipeline
OTEL_SERVICE_VERSION=1.0.0
```

### Environment Variable Checklist

Before deployment, verify:
- ✅ All REQUIRED variables are set (no placeholder values)
- ✅ ELASTICSEARCH_URL uses HTTPS
- ✅ CORS_ORIGINS uses HTTPS (not wildcard in production)
- ✅ API keys are valid and at least the minimum length
- ✅ LOG_LEVEL is INFO or higher (not DEBUG in production)
- ✅ PORT is not privileged (<1024)
- ✅ REQUEST_TIMEOUT_SECONDS is 30-60 seconds
- ✅ Secrets are injected via platform, NOT committed to repo

---

## Docker Deployment

### Building the Docker Image

```bash
# Build the Docker image
docker build -t nexus-rag-pipeline:latest .
docker build -t nexus-rag-pipeline:1.0.0 .

# Push to registry (optional)
docker tag nexus-rag-pipeline:latest myregistry/nexus-rag-pipeline:latest
docker push myregistry/nexus-rag-pipeline:latest
```

### Running Locally

```bash
# Create .env file with your configuration
cat > .env << EOF
ENVIRONMENT=production
GEMINI_API_KEY=your_key
ELASTICSEARCH_URL=your_url
ELASTICSEARCH_API_KEY=your_key
# ... other variables
EOF

# Run the container
docker run -p 8000:8000 \
  --env-file .env \
  --name nexus-rag \
  nexus-rag-pipeline:latest

# Run with health check
docker run -p 8000:8000 \
  --env-file .env \
  --health-cmd='curl -f http://localhost:8000/health || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --name nexus-rag \
  nexus-rag-pipeline:latest
```

### Docker Compose Deployment

```yaml
version: '3.8'
services:
  nexus-rag:
    build: .
    image: nexus-rag-pipeline:latest
    container_name: nexus-rag-pipeline
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: production
      LOG_LEVEL: INFO
      PORT: 8000
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      ELASTICSEARCH_URL: ${ELASTICSEARCH_URL}
      ELASTICSEARCH_API_KEY: ${ELASTICSEARCH_API_KEY}
      ELASTICSEARCH_INDEX: nexus-rag-documents-prod
      RETRIEVE_K: "5"
      MAX_RAG_ROUNDS: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - nexus-network
    # Optional: Add volume for logs
    volumes:
      - ./logs:/app/logs

networks:
  nexus-network:
    driver: bridge
```

Run with Docker Compose:
```bash
docker-compose up -d
docker-compose logs -f nexus-rag
docker-compose down
```

### Docker Registry Options

#### Docker Hub
```bash
docker tag nexus-rag-pipeline:latest yourname/nexus-rag-pipeline:latest
docker login
docker push yourname/nexus-rag-pipeline:latest
```

#### AWS ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag nexus-rag-pipeline:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/nexus-rag-pipeline:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/nexus-rag-pipeline:latest
```

#### Google Container Registry (GCR)
```bash
docker tag nexus-rag-pipeline:latest gcr.io/your-project/nexus-rag-pipeline:latest
docker push gcr.io/your-project/nexus-rag-pipeline:latest
```

---

## Render Platform Deployment

Render is the recommended platform for quick and managed deployment.

### Step-by-Step Deployment

#### 1. Prepare Your Repository
```bash
# Ensure Render configuration exists
ls -la render.yaml
cat render.yaml
```

#### 2. Create Render Account
- Go to https://render.com
- Sign up with GitHub account
- Authorize Render to access your repositories

#### 3. Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select the `nexus-rag-pipeline` repository
4. Set service name: `nexus-rag-pipeline`

#### 4. Configure Build Settings
| Setting | Value |
|---------|-------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Plan | Standard or Free (starter) |

#### 5. Set Environment Variables
In Render dashboard → Environment:

```
ENVIRONMENT=production
LOG_LEVEL=INFO
GEMINI_API_KEY=<paste-your-key>
ELASTICSEARCH_URL=https://your-cluster.es.region.cloud.es.io:443
ELASTICSEARCH_API_KEY=<paste-your-key>
ELASTICSEARCH_INDEX=nexus-rag-documents-prod
GEMINI_MODEL=gemini-3.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_TEMPERATURE=0.2
MAX_RAG_ROUNDS=3
RETRIEVE_K=5
CORS_ORIGINS=https://yourdomain.com
```

#### 6. Configure Health Checks
- Health Check Path: `/health`
- Health Check Timeout: `10` seconds
- Interval: `30` seconds

#### 7. Deploy
- Click "Create Web Service"
- Render will build and deploy automatically
- Monitor logs in real-time
- Once status is "Live", your service is deployed

#### 8. Get Your URL
```
https://nexus-rag-pipeline-xxxx.onrender.com
```

### Render Deployment Best Practices

- **Auto-deploy**: Enable to auto-deploy on git push
- **Environment sync**: Disable for sensitive variables
- **Restart policy**: Set to "Auto"
- **Cron jobs**: Use for backup scheduling if needed
- **Private services**: Consider for internal endpoints

### Access Your Deployed Service

```bash
SERVICE_URL=https://nexus-rag-pipeline-xxxx.onrender.com

# Test health
curl $SERVICE_URL/health

# Access UI
open $SERVICE_URL/app

# Access API docs
open $SERVICE_URL/docs

# Test query endpoint
curl -X POST $SERVICE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}'
```

---

## Kubernetes Deployment (Optional)

For enterprise-grade deployments with high availability.

### Kubernetes Manifests

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus-rag-deployment
  namespace: default
  labels:
    app: nexus-rag
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: nexus-rag
  template:
    metadata:
      labels:
        app: nexus-rag
        version: v1.0.0
    spec:
      serviceAccountName: nexus-rag-sa
      containers:
      - name: nexus-rag
        image: nexus-rag-pipeline:1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: PORT
          value: "8000"
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: nexus-rag-secrets
              key: gemini-api-key
        - name: ELASTICSEARCH_URL
          valueFrom:
            secretKeyRef:
              name: nexus-rag-secrets
              key: elasticsearch-url
        - name: ELASTICSEARCH_API_KEY
          valueFrom:
            secretKeyRef:
              name: nexus-rag-secrets
              key: elasticsearch-api-key
        - name: ELASTICSEARCH_INDEX
          value: "nexus-rag-documents-prod"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]

---
apiVersion: v1
kind: Service
metadata:
  name: nexus-rag-service
  namespace: default
spec:
  selector:
    app: nexus-rag
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  type: LoadBalancer

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: nexus-rag-sa
  namespace: default

---
apiVersion: v1
kind: Secret
metadata:
  name: nexus-rag-secrets
  namespace: default
type: Opaque
stringData:
  gemini-api-key: "your-key"
  elasticsearch-url: "your-url"
  elasticsearch-api-key: "your-key"

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nexus-rag-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nexus-rag-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace nexus-rag

# Apply manifests
kubectl apply -f deployment.yaml -n nexus-rag

# Monitor deployment
kubectl rollout status deployment/nexus-rag-deployment -n nexus-rag

# Get service URL
kubectl get svc nexus-rag-service -n nexus-rag

# View logs
kubectl logs -f deployment/nexus-rag-deployment -n nexus-rag
```

---

## Pre-Flight Checks

Before deploying to production, run these validation checks:

### Configuration Validation Script

Save as `validate_deployment.sh`:

```bash
#!/bin/bash

set -e

echo "=== Nexus RAG Pipeline - Deployment Validation ==="
echo ""

# Check 1: Environment variables
echo "[1/7] Checking environment variables..."
required_vars=("ENVIRONMENT" "GEMINI_API_KEY" "ELASTICSEARCH_URL" "ELASTICSEARCH_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done
echo "✅ All required variables are set"
echo ""

# Check 2: API key lengths
echo "[2/7] Validating API key lengths..."
if [ ${#GEMINI_API_KEY} -lt 30 ]; then
    echo "❌ GEMINI_API_KEY is too short (min 30 chars)"
    exit 1
fi
echo "✅ GEMINI_API_KEY length valid"
echo ""

# Check 3: URLs
echo "[3/7] Validating URLs..."
if [[ ! $ELASTICSEARCH_URL =~ ^https:// ]]; then
    echo "❌ ELASTICSEARCH_URL must use HTTPS"
    exit 1
fi
echo "✅ URLs use HTTPS"
echo ""

# Check 4: CORS origins
echo "[4/7] Validating CORS origins..."
if [[ $CORS_ORIGINS == "*" ]]; then
    echo "⚠️  WARNING: CORS_ORIGINS is wildcard (not recommended for production)"
fi
echo "✅ CORS origins validated"
echo ""

# Check 5: Environment setting
echo "[5/7] Checking environment setting..."
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "staging" ]]; then
    echo "⚠️  WARNING: ENVIRONMENT should be 'production' or 'staging'"
fi
echo "✅ Environment setting: $ENVIRONMENT"
echo ""

# Check 6: Log level
echo "[6/7] Checking log level..."
if [ "$LOG_LEVEL" = "DEBUG" ]; then
    echo "⚠️  WARNING: DEBUG log level in production wastes resources"
fi
echo "✅ Log level: ${LOG_LEVEL:-INFO}"
echo ""

# Check 7: Port
echo "[7/7] Validating port..."
if [ -z "$PORT" ]; then
    echo "⚠️  Using default port 8000"
elif [ $PORT -lt 1024 ]; then
    echo "❌ Port must be >= 1024 (non-privileged)"
    exit 1
fi
echo "✅ Port is valid: ${PORT:-8000}"
echo ""

echo "═══════════════════════════════════════════════"
echo "✅ All pre-flight checks passed!"
echo "═══════════════════════════════════════════════"
```

Run it:
```bash
bash validate_deployment.sh
```

---

## Health Check Procedures

### Basic Health Check

```bash
curl http://localhost:8000/health
```

### Comprehensive Health Check Response

The `/health` endpoint returns:

```json
{
  "status": "ok",
  "timestamp": 1234567890.123,
  "checks": {
    "gemini_configured": true,
    "gemini_api_available": true,
    "elasticsearch_configured": true,
    "elasticsearch_reachable": true,
    "elasticsearch_latency_ms": 45.23
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

### Health Check Status Codes

| Status | Code | Meaning |
|--------|------|---------|
| `ok` | 200 | All systems operational |
| `degraded` | 503 | Partial failure (non-critical systems down) |
| `unhealthy` | 503 | Critical system failure |

### Health Check Monitoring Script

Save as `monitor_health.sh`:

```bash
#!/bin/bash

SERVICE_URL=${1:-http://localhost:8000}
CHECK_INTERVAL=${2:-30}

while true; do
    echo "[$(date)]"
    response=$(curl -s -w "\n%{http_code}" $SERVICE_URL/health)
    body=$(echo "$response" | head -n 1)
    code=$(echo "$response" | tail -n 1)
    
    echo "Status Code: $code"
    
    if [ "$code" = "200" ]; then
        echo "✅ Service is healthy"
    elif [ "$code" = "503" ]; then
        echo "⚠️  Service is degraded"
    else
        echo "❌ Service is unreachable"
    fi
    
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    echo "---"
    sleep $CHECK_INTERVAL
done
```

Usage:
```bash
bash monitor_health.sh https://nexus-rag-pipeline-xxxx.onrender.com 60
```

---

## Monitoring Setup

### Key Metrics to Monitor

```
Application Metrics:
├── Request Rate (req/sec)
├── Error Rate (%)
├── Response Time (p50, p95, p99)
├── Active Connections
└── Memory Usage (%)

Elasticsearch Metrics:
├── Query Latency
├── Index Size
├── Document Count
├── JVM Memory
└── Cluster Health

Gemini API Metrics:
├── API Response Time
├── Error Rate
├── Token Usage
└── Rate Limit Status
```

### Prometheus Metrics Endpoint

Add to your monitoring:
```bash
curl http://localhost:8000/metrics
```

Response includes:
- Query count and latency
- Document ingestion metrics
- Error counts by type
- Cache hit rates

### Setting Up Monitoring

#### Using CloudWatch (AWS)
```bash
pip install watchtower
```

Update your application configuration:
```python
import watchtower
logging.getLogger().addHandler(
    watchtower.CloudWatchLogHandler()
)
```

#### Using ELK Stack
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/nexus-rag/*.log
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

#### Using Datadog
```bash
pip install datadog
```

---

## Backup & Recovery

### Elasticsearch Backup Strategy

#### Daily Snapshots
```bash
#!/bin/bash
# backup_elasticsearch.sh

SNAPSHOT_REPO="s3://your-backup-bucket/es-snapshots"
ES_URL="https://your-cluster.es.region.cloud.es.io:443"
ES_USER="elastic"
ES_PASSWORD="your-password"

# Create snapshot repository
curl -u $ES_USER:$ES_PASSWORD -X PUT \
  "$ES_URL/_snapshot/s3-repo" \
  -H 'Content-Type: application/json' \
  -d "{ \"type\": \"s3\", \"settings\": { \"bucket\": \"$SNAPSHOT_REPO\" } }"

# Create snapshot
SNAPSHOT_NAME="snapshot-$(date +%Y%m%d-%H%M%S)"
curl -u $ES_USER:$ES_PASSWORD -X PUT \
  "$ES_URL/_snapshot/s3-repo/$SNAPSHOT_NAME" \
  -H 'Content-Type: application/json'

echo "Snapshot created: $SNAPSHOT_NAME"
```

Schedule with cron:
```bash
# Daily at 2 AM
0 2 * * * /path/to/backup_elasticsearch.sh
```

#### Recovery Procedure
```bash
#!/bin/bash
# restore_elasticsearch.sh

SNAPSHOT_NAME=$1
ES_URL="https://your-cluster.es.region.cloud.es.io:443"
ES_USER="elastic"
ES_PASSWORD="your-password"

if [ -z "$SNAPSHOT_NAME" ]; then
    echo "Usage: $0 <snapshot-name>"
    echo "Available snapshots:"
    curl -u $ES_USER:$ES_PASSWORD "$ES_URL/_snapshot/s3-repo/_all"
    exit 1
fi

# Close indices
curl -u $ES_USER:$ES_PASSWORD -X POST \
  "$ES_URL/_all/_close"

# Restore snapshot
curl -u $ES_USER:$ES_PASSWORD -X POST \
  "$ES_URL/_snapshot/s3-repo/$SNAPSHOT_NAME/_restore" \
  -H 'Content-Type: application/json'

echo "Restoring snapshot: $SNAPSHOT_NAME"
```

### Application Backup

```bash
#!/bin/bash
# backup_application.sh

BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp .env.production $BACKUP_DIR/
cp render.yaml $BACKUP_DIR/
cp requirements.txt $BACKUP_DIR/

# Backup Dockerfile
cp Dockerfile $BACKUP_DIR/

# Upload to S3 (or other storage)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/app-backups/ --delete

echo "Application backed up to $BACKUP_DIR"
```

### Disaster Recovery Plan

| Component | RTO | RPO | Recovery Steps |
|-----------|-----|-----|-----------------|
| **Application** | 15 min | 1 hour | Redeploy from backup config |
| **Elasticsearch** | 30 min | 24 hours | Restore latest snapshot |
| **Configuration** | 5 min | 1 min | Restore from version control |

#### Recovery Checklist

- [ ] Restore Elasticsearch from latest snapshot
- [ ] Update application configuration
- [ ] Redeploy application containers
- [ ] Run health checks
- [ ] Verify data integrity
- [ ] Monitor error rates
- [ ] Notify stakeholders

---

## Scaling Recommendations

### Vertical Scaling (Increase Resources)

```yaml
# Kubernetes: Update resource limits
resources:
  requests:
    cpu: 1000m      # Increase from 500m
    memory: 1Gi     # Increase from 512Mi
  limits:
    cpu: 2000m      # Increase from 1000m
    memory: 2Gi     # Increase from 1Gi
```

### Horizontal Scaling (Add Instances)

#### Render Scaling
- ✅ Automatic with Standard plan
- Scales based on CPU/memory
- No manual configuration needed

#### Kubernetes Scaling
```yaml
# HorizontalPodAutoscaler already configured
# Scales from 3 to 10 replicas based on load
```

#### Docker Compose Scaling
```bash
# Scale to 5 instances
docker-compose up -d --scale nexus-rag=5
```

### Performance Tuning

#### Query Performance
```
# If queries are slow:
1. Increase RETRIEVE_K slightly
2. Optimize Elasticsearch queries
3. Add caching for common queries
4. Increase Gemini token limits
```

#### Memory Optimization
```python
# Update backend config:
CHUNK_SIZE_CHARS=1200      # Reduce from 1600
CHUNK_OVERLAP_CHARS=100    # Reduce from 200
RETRIEVE_K=3               # Reduce from 5
```

#### Connection Pooling
```python
# Elasticsearch connection pool
es = Elasticsearch(
    [settings.elasticsearch_url],
    request_timeout=30,
    connection_pool_kwargs={"maxsize": 25}
)
```

### Load Balancing

#### Render Built-in Load Balancing
- ✅ Automatic load balancing
- ✅ Health-based routing
- ✅ Sticky sessions support

#### Kubernetes Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nexus-rag-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: nexus-rag.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nexus-rag-service
            port:
              number: 80
```

### Recommended Instance Sizes

| Traffic | Instances | CPU | Memory | Notes |
|---------|-----------|-----|--------|-------|
| < 100 req/min | 1 | 0.5 vCPU | 512 MB | Staging/demo |
| 100-1000 req/min | 2-3 | 1 vCPU | 1 GB | Small production |
| 1000-5000 req/min | 5-10 | 2 vCPU | 2 GB | Medium production |
| > 5000 req/min | 10+ | 4+ vCPU | 4+ GB | Enterprise |

---

## Troubleshooting Guide

### Common Issues & Solutions

#### 1. Health Check Failing

**Symptoms:**
```
❌ /health returns 503
```

**Diagnosis:**
```bash
# Check Elasticsearch connection
curl https://your-elasticsearch-url:9200/_ping

# Check Gemini API status
# Visit: https://console.cloud.google.com

# Check application logs
docker logs nexus-rag
# Or:
kubectl logs deployment/nexus-rag-deployment
```

**Solutions:**
- ✅ Verify Elasticsearch URL and API key
- ✅ Check network connectivity to ES
- ✅ Verify Gemini API key is valid
- ✅ Check firewall rules

#### 2. Query Timeout

**Symptoms:**
```
❌ Query takes > 30 seconds
```

**Diagnosis:**
```bash
# Monitor slow queries
curl http://localhost:8000/metrics | jq '.query_latency'

# Check Elasticsearch performance
curl -u elastic:password \
  https://your-es-url/_cat/indices?v
```

**Solutions:**
- ✅ Increase REQUEST_TIMEOUT_SECONDS
- ✅ Reduce RETRIEVE_K
- ✅ Optimize Elasticsearch query
- ✅ Check Elasticsearch cluster health

#### 3. Memory Leak

**Symptoms:**
```
⚠️ Memory usage continuously increasing
```

**Diagnosis:**
```bash
# Monitor memory with Docker
docker stats nexus-rag

# Check for connection leaks
curl http://localhost:8000/metrics | jq '.connection_pool'
```

**Solutions:**
- ✅ Reduce CHUNK_SIZE_CHARS
- ✅ Implement connection pooling
- ✅ Update stale dependencies
- ✅ Add memory limits to container

#### 4. Rate Limiting

**Symptoms:**
```
❌ 429 Too Many Requests
```

**Diagnosis:**
```bash
# Check rate limit headers
curl -i http://localhost:8000/query

# View rate limit configuration
curl http://localhost:8000/metrics | jq '.rate_limit'
```

**Solutions:**
- ✅ Implement backoff/retry logic
- ✅ Increase RATE_LIMIT_REQUESTS_PER_MINUTE
- ✅ Add IP whitelisting
- ✅ Implement caching to reduce requests

#### 5. Document Upload Failure

**Symptoms:**
```
❌ /documents endpoint returns 500
```

**Diagnosis:**
```bash
# Check file size
ls -lh problematic_file.pdf

# Check Elasticsearch index
curl -u elastic:password \
  https://your-es-url/nexus-rag-documents/_settings
```

**Solutions:**
- ✅ Verify file size < MAX_BODY_SIZE_MB
- ✅ Check file format is supported
- ✅ Verify Elasticsearch index exists
- ✅ Check available disk space

### Debugging Commands

```bash
# View application logs
docker logs -f nexus-rag --tail=100

# Kubernetes logs
kubectl logs -f pod/nexus-rag-xxxxx -n default

# Check Docker resource usage
docker stats nexus-rag

# Test Elasticsearch connection
curl -u elastic:password -X GET \
  https://your-es-url:9200/_cluster/health

# Test Gemini API
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models/gemini-3.5-flash/generateContent

# Profile memory usage
python -m memory_profiler backend/main.py

# Run security scan
pip install safety
safety check -r requirements.txt
```

### Log Level Configuration

```bash
# Production
LOG_LEVEL=INFO

# Development
LOG_LEVEL=DEBUG

# Minimal logging
LOG_LEVEL=WARNING

# Errors only
LOG_LEVEL=ERROR
```

---

## Pre-Deployment Requirements

This section ensures your deployment meets production standards for security, monitoring, and operational reliability.

### Configuration & Secrets

- [ ] **Environment**: Copy `.env.production` template to your deployment platform's secret manager
  - Never commit `.env.production` with real values to version control
  - Use platform-specific secret injection (Render, AWS Secrets Manager, Azure Key Vault, etc.)
  - Validate all required fields are populated (no empty values)

- [ ] **API Keys & Credentials**
  - [ ] GEMINI_API_KEY is valid and has "Generative Language API" permissions
  - [ ] ELASTICSEARCH_URL uses HTTPS (not HTTP) in production
  - [ ] ELASTICSEARCH_API_KEY has minimal required permissions (read/write on target index)
  - [ ] API keys are at least 32 characters (validate in secret manager)
  - [ ] Rotate credentials at least every 90 days

- [ ] **Network Security**
  - [ ] CORS_ORIGINS is specific (not `*` in production) and uses HTTPS
  - [ ] Firewall rules restrict access to Elasticsearch to only your app
  - [ ] SSL/TLS certificates are valid and not self-signed for Elasticsearch
  - [ ] Enable HTTPS for your service URL (SSL certificate provisioned)

### Application Configuration

- [ ] **Environment Settings**
  - [ ] ENVIRONMENT=production
  - [ ] LOG_LEVEL=INFO (not DEBUG - verbose logging in production wastes resources)
  - [ ] PORT is not privileged (<1024) and available on host
  - [ ] REQUEST_TIMEOUT_SECONDS is 30-60 seconds (reasonable for RAG)

- [ ] **Rate Limiting**
  - [ ] RATE_LIMIT_ENABLED=true
  - [ ] RATE_LIMIT_REQUESTS_PER_MINUTE is reasonable for your use case (default: 60)
  - [ ] RATE_LIMIT_REQUESTS_PER_HOUR prevents abuse (default: 1000)
  - [ ] Consider Redis-based rate limiting for multi-instance deployments

- [ ] **Performance Tuning**
  - [ ] RETRIEVE_K (5-10) balances relevance vs latency
  - [ ] MAX_RAG_ROUNDS limited to 3 (prevents infinite refinement loops)
  - [ ] CHUNK_SIZE_CHARS and CHUNK_OVERLAP_CHARS optimized for your documents
  - [ ] Elasticsearch shards distributed across nodes for production cluster

### Security & Compliance

- [ ] **Security Headers**
  - [ ] X-Frame-Options: DENY (clickjacking protection) ✓ Configured
  - [ ] X-Content-Type-Options: nosniff (MIME sniffing protection) ✓ Configured
  - [ ] X-XSS-Protection: 1; mode=block ✓ Configured
  - [ ] Content-Security-Policy configured for your frontend domain ✓ Configured
  - [ ] Strict-Transport-Security enabled (HSTS) ✓ Configured

- [ ] **Input Validation**
  - [ ] Query length limits enforced (max 2000 chars recommended)
  - [ ] File upload size limits enforced (MAX_BODY_SIZE_MB=100)
  - [ ] Special characters in queries are escaped
  - [ ] Elasticsearch index names are validated

- [ ] **Data Protection**
  - [ ] Logs do NOT contain API keys or sensitive data (check log output)
  - [ ] Error messages don't leak internal structure to clients
  - [ ] Database passwords never appear in error responses
  - [ ] User queries are not logged verbatim (only sanitized summaries)

### Infrastructure & Deployment

- [ ] **Health Checks**
  - [ ] /health endpoint accessible without authentication ✓ Configured
  - [ ] Deployment platform configured to call /health every 30 seconds
  - [ ] Health check response includes dependency status (Elasticsearch, Gemini)
  - [ ] Unhealthy instances are automatically removed from load balancer

- [ ] **Monitoring & Logging**
  - [ ] Structured logging enabled for centralized log aggregation
  - [ ] Application logs sent to: _________________ (CloudWatch, ELK, Datadog, etc)
  - [ ] Metrics exported to: _________________ (Prometheus, Datadog, New Relic, etc)
  - [ ] Alerts configured for:
    - [ ] Error rate > 1%
    - [ ] Response time > 5 seconds
    - [ ] Elasticsearch unavailable
    - [ ] Rate limit violations

- [ ] **Backup & Disaster Recovery**
  - [ ] Elasticsearch snapshots scheduled daily to external storage (S3, GCS)
  - [ ] Restore procedure tested and documented
  - [ ] RTO (Recovery Time Objective) < 1 hour
  - [ ] RPO (Recovery Point Objective) < 24 hours

- [ ] **Load Balancing**
  - [ ] Application deployed on 2+ instances (high availability)
  - [ ] Load balancer configured with health checks
  - [ ] Connection pooling configured for Elasticsearch (prevent connection exhaustion)
  - [ ] Circuit breaker pattern implemented for Elasticsearch failures

### Testing & Validation

- [ ] **Functional Testing**
  - [ ] Query endpoint returns correct results
  - [ ] Document upload processes successfully
  - [ ] Health check passes with all dependencies
  - [ ] Error handling returns appropriate HTTP status codes

- [ ] **Load Testing**
  - [ ] Application handles 60 req/min without degradation
  - [ ] Latency stays under 5 seconds at peak load
  - [ ] Memory usage stays under 512MB (adjust for your instance type)
  - [ ] No connection leaks to Elasticsearch

- [ ] **Security Testing**
  - [ ] SQL injection attempts are rejected
  - [ ] XSS payloads are escaped
  - [ ] CORS policy enforced (wrong origin requests rejected)
  - [ ] Rate limiting blocks abusive clients

## Post-Deployment Verification

After deploying, run these checks:

```bash
# Check service health
curl https://your-service-url/health

# Check API documentation available
curl https://your-service-url/docs

# Test a simple query
curl -X POST https://your-service-url/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","top_k":5}'

# Verify security headers
curl -I https://your-service-url/
# Look for: X-Frame-Options, X-Content-Type-Options, Content-Security-Policy
```

## Monitoring Dashboard

Set up monitoring for these key metrics:

| Metric | Alert Threshold | What It Means |
|--------|-----------------|---------------|
| Error Rate | > 1% | More than 1 in 100 requests fail |
| Query Latency (p99) | > 5s | Slow queries affecting users |
| Elasticsearch Latency | > 500ms | Retrieval is slow |
| Rate Limit Hits | > 10/hour | Possible DDoS or abuse |
| Health Check Failures | 2 consecutive | Service is degraded |
| Memory Usage | > 75% | Memory leak or underprovisioned |

## Incident Response

### When Health Check Fails

1. Check Elasticsearch connectivity: `curl https://elasticsearch-url`
2. Check Gemini API status: API dashboard
3. Review logs for error patterns
4. If ES is down: redirect traffic to backup cluster if available
5. If Gemini is down: mark service as degraded, continue retrieval only

### When Rate Limiting Triggers

1. Review logs for source IPs
2. Check if legitimate traffic spike or attack
3. Increase limits if spike is expected
4. Block IPs making requests outside normal pattern (DDoS)

### When Latency Spikes

1. Check Elasticsearch cluster health
2. Review active query count (may need more shards)
3. Check if query complexity increased
4. Verify no network issues between app and ES

## Production Standards Met

✓ Security headers (OWASP)  
✓ Rate limiting (ready to enable)  
✓ Structured logging stubs (implement with your backend)  
✓ OpenTelemetry hooks (implement with your backend)  
✓ Enhanced health checks with dependency status  
✓ Production environment template with validation  
✓ Deployment checklist for consistency  

## Additional Resources

- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Elasticsearch Security](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-overview.html)
- [OpenTelemetry Documentation](https://opentelemetry.io/)


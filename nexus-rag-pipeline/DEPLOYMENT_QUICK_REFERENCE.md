# Quick Deployment Reference

**Nexus RAG Pipeline - Quick Start Deployment Guide**

## 🚀 5-Minute Deploy

### 1. Local (Docker)
```bash
# Build
docker build -t nexus-rag-pipeline .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e ELASTICSEARCH_URL=your_url \
  -e ELASTICSEARCH_API_KEY=your_key \
  nexus-rag-pipeline

# Test
curl http://localhost:8000/health
```

### 2. Render Platform (Recommended)
```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to Render"
git push origin main

# 2. Go to https://render.com
# 3. Create New → Web Service
# 4. Connect your repository
# 5. Set environment variables:
GEMINI_API_KEY=your_key
ELASTICSEARCH_URL=your_url
ELASTICSEARCH_API_KEY=your_key

# 6. Deploy (auto-deploys on git push)

# Test
curl https://nexus-rag-pipeline-xxxx.onrender.com/health
```

### 3. Kubernetes
```bash
# 1. Update secrets in deployment.yaml
# 2. Deploy
kubectl apply -f deployment.yaml

# 3. Get URL
kubectl get svc nexus-rag-service
```

---

## ⚡ Pre-Deployment Checklist

- [ ] All environment variables set
- [ ] ELASTICSEARCH_URL uses HTTPS
- [ ] GEMINI_API_KEY is valid (min 30 chars)
- [ ] CORS_ORIGINS does not use wildcard
- [ ] LOG_LEVEL is INFO (not DEBUG)
- [ ] Run: `python scripts/validate_deployment.py`
- [ ] Health check passes

---

## 📊 Monitoring Commands

```bash
# Health check
curl https://your-service-url/health

# Metrics
curl https://your-service-url/metrics | jq

# API docs
open https://your-service-url/docs

# Logs (Docker)
docker logs -f nexus-rag --tail=100

# Logs (Kubernetes)
kubectl logs -f deployment/nexus-rag-deployment

# Monitor health
python scripts/health_monitor.py https://your-service-url 30
```

---

## 🔧 Configuration Quick Reference

| Variable | Value | Notes |
|----------|-------|-------|
| ENVIRONMENT | production | Required |
| LOG_LEVEL | INFO | Not DEBUG |
| GEMINI_MODEL | gemini-3.5-flash | Required |
| ELASTICSEARCH_INDEX | nexus-rag-documents-prod | Per environment |
| RETRIEVE_K | 5 | 1-20 |
| MAX_RAG_ROUNDS | 3 | 1-3 |
| RATE_LIMIT_REQUESTS_PER_MINUTE | 60 | Adjust for load |
| RATE_LIMIT_REQUESTS_PER_HOUR | 1000 | Adjust for load |

---

## 🐛 Common Issues

### Health Check Fails (503)
```bash
# 1. Check Elasticsearch
curl https://your-elasticsearch-url/_ping

# 2. Check Gemini API key
echo $GEMINI_API_KEY

# 3. Check logs
docker logs nexus-rag
```

### Query Timeout
- Reduce RETRIEVE_K
- Increase REQUEST_TIMEOUT_SECONDS
- Check Elasticsearch performance

### Memory Usage High
- Reduce CHUNK_SIZE_CHARS
- Increase container memory limit
- Check for connection leaks

### Rate Limited (429)
- Implement client-side retry/backoff
- Increase RATE_LIMIT_REQUESTS_PER_MINUTE
- Whitelist trusted IPs

---

## 📋 Deployment Endpoints

```
Status: GET /
Health: GET /health
Metrics: GET /metrics
Docs: GET /docs
Query: POST /query
Upload: POST /documents
List: GET /documents
Evaluate: POST /evaluate
```

---

## 🔐 Security Checklist

- ✅ HTTPS only for all external URLs
- ✅ API keys not in version control
- ✅ Secrets injected via platform
- ✅ CORS limited to specific origins
- ✅ Security headers enabled
- ✅ Rate limiting enabled
- ✅ Health check runs regularly

---

## 📞 Support Resources

- **Documentation**: See DEPLOYMENT.md
- **API Reference**: {service-url}/docs
- **Health Status**: {service-url}/health
- **Render Support**: https://render.com/docs
- **Elasticsearch Docs**: https://www.elastic.co/guide/
- **Gemini API Docs**: https://developers.google.com/gen-ai

---

## 🎯 Success Criteria

✅ Deployment is successful when:
1. Health check returns 200 with `status: "ok"`
2. All dependencies are reachable
3. Query endpoint accepts requests
4. Document upload works
5. Logs show no errors
6. Performance metrics are acceptable

---

**Last Updated**: 2024
**Version**: 1.0.0

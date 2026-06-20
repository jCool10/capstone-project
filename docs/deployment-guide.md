# Deployment Guide

## Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git
- 8GB RAM minimum
- 20GB disk space

### 1. Clone & Setup

```bash
git clone <repository-url>
cd capstone-project
cp env.example .env
```

### 2. Configure Environment Variables

Edit `.env`:

```bash
# MongoDB
DB_URL="mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority"

# JWT Token Validity (seconds)
ACCESS_TOKEN_VALIDITY_SEC=3600          # 1 hour
REFRESH_TOKEN_VALIDITY_SEC=86400        # 24 hours

# AWS S3 Credentials
AWS_ACCESS_KEY_ID="your_access_key"
AWS_SECRET_ACCESS_KEY="your_secret_key"
AWS_REGION="us-east-1"
AWS_BUCKET="your_bucket_name"

# Frontend URLs
NEXT_PUBLIC_APP_URL="http://localhost:3000"
NEXT_PUBLIC_API_URL="http://localhost:3001/api"

# RAG Service
EMBEDDING_MODEL="BAAI/bge-base-en-v1.5"
HUGGING_FACE_HUB_TOKEN="your_hf_token"

# Milvus (internal, Docker Compose)
MILVUS_URI="http://milvus:19530"

# Node Environment
NODE_ENV="development"
```

### 3. Build & Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Verify Services Are Healthy

```bash
# Frontend
curl -s http://localhost:3000 | head -20

# Node API
curl -s http://localhost:3001/health

# Python RAG
curl -s http://localhost:8080/

# Milvus
curl -s http://localhost:9091/healthz

# MinIO Console (optional)
open http://localhost:9001  # username: minioadmin, password: minioadmin
```

### 5. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:3001/api
- **RAG Service:** http://localhost:8080
- **MinIO Console:** http://localhost:9001

---

## Development Setup (Local)

### Frontend Development

```bash
cd client
yarn install
yarn dev                    # Starts on http://localhost:3000

# In another terminal
yarn typecheck              # Type checking
yarn lint                   # ESLint
yarn format:check           # Prettier check
```

### Backend API Development

```bash
cd node-server
yarn install
yarn dev                    # Starts on http://localhost:3000 (Express)

# In another terminal
yarn typecheck
yarn lint
yarn prettier
```

### RAG Service Development

```bash
cd python-server
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py          # Starts on http://localhost:8080
```

### Full Stack Local (without Docker)

1. **Start MongoDB locally**
   ```bash
   # macOS with Homebrew
   brew services start mongodb-community
   
   # Or use MongoDB Atlas (cloud)
   # Update DB_URL in .env
   ```

2. **Start Milvus locally (optional)**
   ```bash
   # Use Docker for Milvus only
   docker-compose up milvus etcd minio -d
   ```

3. **Start services in separate terminals**
   ```bash
   # Terminal 1: Frontend
   cd client && yarn dev
   
   # Terminal 2: Backend
   cd node-server && yarn dev
   
   # Terminal 3: RAG
   cd python-server && python app/main.py
   ```

---

## Port Mapping

| Service | Port | Env | Purpose |
|---------|------|-----|---------|
| Frontend | 3000 | dev/prod | Next.js app |
| Backend API | 3000 (dev) / 3001 (docker) | dev/prod | Express server |
| RAG Service | 8080 | dev/prod | FastAPI |
| Milvus | 19530 | docker | Vector DB |
| MinIO | 9000 | docker | Object storage |
| MinIO Console | 9001 | docker | MinIO UI |
| ETCD | 2379 | docker | Milvus config |

---

## Health Check Endpoints

| Service | Endpoint | Method | Expected Response |
|---------|----------|--------|-------------------|
| Frontend | `GET /` | GET | HTML page (200) |
| Node API | `GET /health` | GET | `{status: "ok"}` (200) |
| Python RAG | `GET /` | GET | `{message: "Hello World"}` (200) |
| Milvus | `GET /healthz` | GET | 200 |
| MongoDB | ping | - | Connected |

---

## Docker Compose Configuration

### Service Dependency Tree

```
etcd + minio
    ↓
  milvus
    ↓
python-server
    ↓
node-server
    ↓
client (frontend)
```

### Volume Mounts

| Service | Source | Destination | Purpose |
|---------|--------|-------------|---------|
| etcd | `etcd_data` | `/etcd` | ETCD persistence |
| minio | `minio_data` | `/minio_data` | MinIO storage |
| milvus | `milvus_data` | `/var/lib/milvus` | Milvus indexes |
| python-server | `./python-server/data` | `/app/data` | Sample docs, BM25 indices |
| python-server | `./python-server/volumes` | `/app/volumes` | Workspace volumes |
| node-server | `./node-server/uploads` | `/app/uploads` | Temp file uploads |
| node-server | `./node-server/logs` | `/app/logs` | Application logs |

### Environment Injection

**In docker-compose.yml, variables from `.env` are injected:**

```yaml
environment:
  - DB_URL=${DB_URL}
  - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  - MILVUS_URI=${MILVUS_URI:-http://milvus:19530}
```

---

## Troubleshooting

### 1. Services Won't Start

**Issue:** `Error response from daemon: OCI runtime create failed`

**Solution:**
```bash
# Check Docker daemon is running
docker ps

# Restart Docker
docker restart

# Try again
docker-compose up -d
```

### 2. Milvus Health Check Failing

**Issue:** Milvus keeps restarting

```bash
# Check Milvus logs
docker-compose logs milvus

# Increase start_period in docker-compose.yml
# Milvus may need 120s+ to fully initialize
```

**Solution:** Increase `start_period` in `docker-compose.yml`:
```yaml
milvus:
  healthcheck:
    start_period: 180s  # Increase from 90s
```

### 3. Python Service Can't Connect to Milvus

**Issue:** `pymilvus.exceptions.MilvusException: Unable to connect to Milvus`

**Solution:**
```bash
# Check Milvus is running and healthy
docker-compose logs milvus

# Verify MILVUS_URI environment variable
docker-compose exec python-server printenv MILVUS_URI

# Should output: http://milvus:19530
```

### 4. Node API Can't Connect to MongoDB

**Issue:** `MongoError: connect ECONNREFUSED 127.0.0.1:27017`

**Solution:**
- If using local MongoDB: Start MongoDB service (`brew services start mongodb-community`)
- If using MongoDB Atlas: Verify `DB_URL` in `.env` is correct
- Check connection string format: `mongodb+srv://user:password@host/?options`

### 5. Frontend Can't Call Backend API

**Issue:** CORS error in browser console

**Solution:**
```bash
# Verify backend is running
curl -s http://localhost:3001/health

# Check NEXT_PUBLIC_API_URL in .env
# Should be: http://localhost:3001/api

# Verify NODE_CORS settings in node-server
# Should include localhost:3000
```

### 6. Out of Memory

**Issue:** Services crashing with OOM

**Solution:**
```bash
# Increase Docker Desktop memory limit
# Docker Desktop → Preferences → Resources → Memory → Increase to 8GB+

# Or increase Node.js heap size
# In node-server/Dockerfile:
ENV NODE_OPTIONS="--max-old-space-size=2048"
```

### 7. File Upload Failing

**Issue:** 413 Payload Too Large or S3 upload fails

**Solution:**
```bash
# Check S3 credentials in .env
# Verify bucket exists and is accessible
aws s3 ls s3://your_bucket_name --profile default

# Check file size limit (max 100MB per workspace)
# Multer config in node-server/src/middlewares/multer.middleware.ts
```

---

## Logging & Monitoring

### Node.js Logs (Winston)

Logs saved to `./node-server/logs/app-YYYY-MM-DD.log`:

```bash
# Tail logs
tail -f node-server/logs/app-*.log

# Search for errors
grep ERROR node-server/logs/app-*.log
```

### Python Logs

Visible in Docker logs:

```bash
# View RAG service logs
docker-compose logs python-server

# Follow in real-time
docker-compose logs -f python-server
```

### Docker Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs node-server

# Follow (-f) and limit lines (-n)
docker-compose logs -f -n 100 milvus
```

### Health Check Failures

```bash
# Check health status
docker-compose ps

# If unhealthy, view health logs
docker inspect capstone_node_server | jq '.State.Health'

# Restart unhealthy service
docker-compose restart node-server
```

---

## Backup & Restore

### MongoDB Backup

```bash
# Backup local MongoDB
mongodump --db capstone --out ./backups/mongo/

# Restore
mongorestore --db capstone ./backups/mongo/capstone/
```

### Milvus Data Backup

Milvus data persists in named volume `milvus_data`. To back up:

```bash
# Create backup volume
docker run --rm -v milvus_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/milvus_data.tar.gz -C /data .

# Restore
docker run --rm -v milvus_data:/data -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/milvus_data.tar.gz -C /data
```

### S3 Files Backup

```bash
# Sync S3 bucket locally
aws s3 sync s3://your_bucket_name ./backups/s3/ \
  --profile default --region us-east-1
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Instances)

Currently uses Docker Compose (single-machine). For production:

**Migrate to Kubernetes:**
- Frontend: Horizontal Pod Autoscaler (HPA) with 3+ replicas
- Backend API: 5+ replicas with load balancing
- RAG Service: 2+ replicas (GPU-accelerated if needed)
- Milvus: Cluster mode (3+ servers) instead of standalone

**Load Balancer:**
- ALB (AWS) or Nginx Ingress (K8S)
- Route `/api/*` to node-server replicas
- Route `/` to client replicas
- Route `/query`, `/embed` to python-server replicas

### Vertical Scaling (Single Machine)

**Increase resources in docker-compose.yml:**

```yaml
services:
  milvus:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

## Production Checklist

- [ ] Use MongoDB Atlas (managed) instead of local MongoDB
- [ ] Configure AWS S3 bucket with encryption, versioning, lifecycle policies
- [ ] Set up Milvus cluster (3+ nodes) with replication
- [ ] Enable HTTPS for all endpoints (TLS certificates)
- [ ] Rotate JWT keys regularly (use `/api/auth/rotate-keys`)
- [ ] Configure rate limiting on auth endpoints
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Enable audit logging (CloudWatch or equivalent)
- [ ] Use managed Kubernetes (EKS, GKE) instead of Docker Compose
- [ ] Set up automated backups (daily)
- [ ] Configure disaster recovery (RTO/RPO)
- [ ] Run security scan (OWASP ZAP, Snyk)
- [ ] Load test with expected peak traffic
- [ ] Document runbooks for common issues
- [ ] Set up on-call alerting

---

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild images
docker-compose build

# View service status
docker-compose ps

# Check service logs
docker-compose logs -f <service>

# Execute command in service
docker-compose exec <service> <command>

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Scale a service (useful for load testing)
docker-compose up -d --scale python-server=3

# Restart unhealthy services
docker-compose restart node-server python-server

# Full system restart
docker-compose down && docker-compose up -d
```

---

## Environment Variable Reference

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `DB_URL` | - | ✅ | MongoDB connection string |
| `ACCESS_TOKEN_VALIDITY_SEC` | 3600 | ❌ | JWT access token lifetime |
| `REFRESH_TOKEN_VALIDITY_SEC` | 86400 | ❌ | JWT refresh token lifetime |
| `AWS_ACCESS_KEY_ID` | - | ✅ | S3 credentials |
| `AWS_SECRET_ACCESS_KEY` | - | ✅ | S3 credentials |
| `AWS_REGION` | us-east-1 | ❌ | S3 region |
| `AWS_BUCKET` | - | ✅ | S3 bucket name |
| `NEXT_PUBLIC_APP_URL` | http://localhost:3000 | ❌ | Frontend URL |
| `NEXT_PUBLIC_API_URL` | http://localhost:3001/api | ❌ | Backend API URL |
| `EMBEDDING_MODEL` | BAAI/bge-base-en-v1.5 | ❌ | Embedding model name |
| `HUGGING_FACE_HUB_TOKEN` | - | ⚠️ | HuggingFace token (if needed) |
| `MILVUS_URI` | http://milvus:19530 | ❌ | Milvus endpoint (Docker) |
| `NODE_ENV` | development | ❌ | Node environment |

---

## Useful Links

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Milvus Docs](https://milvus.io/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Express Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

See [system-architecture.md](./system-architecture.md) for detailed architecture diagrams.

# DocOps Agent - Docker Setup

## Overview

All services run via Docker Compose for easy development and deployment.

## Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.20
- 8GB RAM minimum
- 20GB disk space

## Quick Start

```bash
# Clone and start all services
git clone https://github.com/yourusername/docops-agent.git
cd docops-agent

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Services

### Service Architecture

```mermaid
flowchart TB
    subgraph External["External (Not in Docker)"]
        Claude["Claude API"]
        OpenAI["OpenAI API"]
        LangSmith["LangSmith"]
    end

    subgraph Docker["Docker Network"]
        API["api<br/>:8000"]
        Worker["worker<br/>(Celery)"]
        Redis["redis<br/>:6379"]
        MinIO["minio<br/>:9000,9001"]
        Postgres["postgres<br/>:5432"]
        Chroma["chroma<br/>:8000"]
    end

    API --> Worker
    Worker --> Redis
    API --> MinIO
    API --> Postgres
    Worker --> Chroma

    Claude -.-> API
    OpenAI -.-> API
    LangSmith -.-> API
```

### Service Details

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| api | custom | 8000 | FastAPI application |
| worker | custom | - | Celery worker |
| redis | redis:7-alpine | 6379 | Task queue broker |
| minio | minio/minio | 9000, 9001 | S3-compatible storage |
| postgres | postgres:16-alpine | 5432 | Metadata database |
| chroma | chromadb/chroma | 8000 | Vector database |

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Required: API Keys (get from respective platforms)
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Optional: LangSmith for tracing
LANGCHAIN_API_KEY=ls-your-key-here
LANGCHAIN_TRACING_V2=true

# Database
DATABASE_URL=postgresql://docops:docops123@postgres:5432/docops

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=docops

# ChromaDB
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: docops
      POSTGRES_PASSWORD: docops123
      POSTGRES_DB: docops
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docops"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis for Celery
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # MinIO for S3-compatible storage
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # ChromaDB for vector storage
  chroma:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma
    ports:
      - "8000:8000"
    environment:
      IS_PERSISTENT: "TRUE"
      ANONYMIZED_TELEMETRY: "FALSE"

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    env_file:
      - .env
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: celery -A src.tasks.celery worker --loglevel=info
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - redis
      - postgres
      - minio
    environment:
      - C_FORCE_ROOT=true

volumes:
  postgres_data:
  minio_data:
  chroma_data:
```

### Dockerfile

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Java for tabula-py
RUN apt-get update && apt-get install -y \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create uploads directory
RUN mkdir -p /app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## MinIO Setup

After starting containers, configure MinIO:

1. Open http://localhost:9001 in browser
2. Login with `minioadmin` / `minioadmin`
3. Create bucket: `docops`
4. Create policy for bucket access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::docops/*"
    }
  ]
}
```

## Database Setup

PostgreSQL tables are created automatically via SQLAlchemy models on first run.

To manually initialize:

```bash
docker-compose exec postgres psql -U docops -d docops -f /docker-entrypoint-initdb.d/init.sql
```

## Verification

### Check all services are healthy

```bash
docker-compose ps
```

Expected output:
```
NAME                IMAGE               STATUS           PORTS
docops-agent-api-1     docops-agent-api-1     running (healthy)   0.0.0.0:8000->8000/tcp
docops-agent-chroma-1   chromadb/chroma        running (healthy)   0.0.0.0:8000->8000/tcp
docops-agent-minio-1    minio/minio            running (healthy)   0.0.0.0:9000->9000/tcp
docops-agent-postgres-1 postgres:16-alpine     running (healthy)   0.0.0.0:5432->5432/tcp
docops-agent-redis-1    redis:7-alpine         running (healthy)   0.0.0.0:6379->6379/tcp
docops-agent-worker-1   docops-agent-worker-1   running           -
```

### Test API health

```bash
curl http://localhost:8000/health
```

### Test MinIO

```bash
curl http://localhost:9000/minio/health/live
```

## Common Issues

### Port conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Map different host port
```

### Out of memory

Increase Docker Desktop memory allocation to 8GB+.

### Permission errors

```bash
sudo chown -R $USER:$USER .
```

## Development Workflow

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Restart a service
docker-compose restart api

# Stop all services
docker-compose down

# Rebuild after dependency changes
docker-compose build --no-cache
```

## Production Considerations

1. **Secrets**: Use Docker secrets or external secret management
2. **Networking**: Use custom network for inter-service communication
3. **Volumes**: Use named volumes for persistent data
4. **Health checks**: Already configured for all services
5. **Logging**: Configure log rotation in production
6. **SSL/TLS**: Add reverse proxy (nginx) for HTTPS

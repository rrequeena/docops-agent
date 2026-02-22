# DocOps Agent - Testing Plan

This document provides instructions for testing the DocOps Agent application.

## Prerequisites

1. **Google API Key**: Get one from https://aistudio.google.com/app/apikey
2. **Docker & Docker Compose** installed
3. **Poetry** installed (for local development)

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/rrequeena/docops-agent.git
cd docops-agent

# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your-key-here
```

### 2. Start Services with Docker Compose

```bash
# Start all services (postgres, redis, minio, chroma, api, worker)
docker-compose up -d

# Verify all services are running
docker-compose ps
```

Expected output:
```
NAME                IMAGE               COMMAND              STATUS
docops-agent-api-1     …                   "uvicorn ..."        Up
docops-agent-minio-1    …                   "/entrypoint.sh …"   Up
docops-agent-postgres-1 …                   "postgres ..."       Up
docops-agent-redis-1    …                   "redis-server …"     Up
docops-agent-worker-1   …                   "celery -A …"        Up
docops-agent-chroma-1   …                   "chroma run …"       Up
```

### 3. Verify Services

```bash
# Test API health endpoint
curl http://localhost:8000/health

# Expected: {"status":"healthy","version":"1.0.0",...}

# Test API root endpoint
curl http://localhost:8000/

# Expected: {"message":"DocOps Agent API","version":"1.0.0"}

# Access the frontend UI
# Open http://localhost:8000/app in your browser
```

## Test Scenarios

### Scenario 1: Document Upload via API

```bash
# Upload a document (replace path to actual file)
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@/path/to/your/document.pdf"

# Expected response:
# {"id":"uuid","filename":"document.pdf","status":"uploaded",...}
```

### Scenario 2: List Documents

```bash
# List all documents
curl http://localhost:8000/api/v1/documents

# Expected: {"documents":[...],"total":N}
```

### Scenario 3: Get Document Details

```bash
# Get specific document (replace UUID)
curl http://localhost:8000/api/v1/documents/<document-uuid>
```

### Scenario 4: Approval Workflow

```bash
# List pending approvals
curl http://localhost:8000/api/v1/approvals

# Approve a request (replace UUID)
curl -X POST http://localhost:8000/api/v1/approvals/<approval-uuid>/approve \
  -H "Content-Type: application/json" \
  -d '{"notes": "Approved for processing"}'

# Reject a request
curl -X POST http://localhost:8000/api/v1/approvals/<approval-uuid>/reject \
  -H "Content-Type: application/json" \
  -d '{"notes": "Missing required fields"}'
```

### Scenario 5: Streamlit UI Testing

1. Open http://localhost:8501
2. Navigate to "Upload" page
3. Upload a PDF invoice
4. Verify the document appears in the list
5. Navigate to "Analysis" page
6. Check for extracted data and anomalies
7. Navigate to "Approvals" page
8. Test approve/reject functionality

## Verification Checklist

- [ ] Docker Compose starts successfully
- [ ] API health check returns healthy
- [ ] Streamlit UI loads at http://localhost:8501
- [ ] Document upload works via API
- [ ] Document upload works via Streamlit
- [ ] Document listing returns correct data
- [ ] Approval workflow functions correctly
- [ ] Extraction results are displayed
- [ ] Analysis shows anomaly detection results

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs -f

# Restart specific service
docker-compose restart api
```

### Database connection issues

```bash
# Check postgres logs
docker-compose logs postgres

# Verify DATABASE_URL in .env
```

### MinIO issues

```bash
# Access MinIO console at http://localhost:9001
# Default credentials: minioadmin/minioadmin

# Check bucket was created
docker-compose logs minio | grep bucket
```

### API returning errors

```bash
# Check API logs
docker-compose logs api

# Verify GOOGLE_API_KEY is set in .env
```

## Running Tests Locally (Without Docker)

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Set environment variables
export GOOGLE_API_KEY=your-key
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin

# Run the API
uvicorn src.api.main:app --reload

# Run tests
pytest tests/
```

## API Documentation

Once the API is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

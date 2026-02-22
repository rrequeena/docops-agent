# (⚠️ WIP ⚠️) DocOps Agent — Multi-Agent System for Automated Document Processing & Analysis

A production-grade multi-agent system where specialized agents collaborate to ingest, extract, analyze, and act on diverse documents with full observability.

## Problem

Enterprises drown in unstructured documents — invoices, contracts, support tickets, compliance docs. Existing solutions break on complex layouts, and production agent systems fail silently. Multi-agent coordination requires careful orchestration to avoid context pollution.

## Solution

DocOps Agent uses LangGraph to orchestrate specialized agents:

- **Supervisor Agent**: Routes tasks, manages state, enforces human approval gates
- **Ingestion Agent**: Classifies document type, extracts text/tables/images, chunks for RAG
- **Extractor Agent**: Maps unstructured content to structured schemas (invoices → JSON)
- **Analyst Agent**: Cross-document analysis, anomaly detection, trend summarization
- **Action Agent**: Generates reports, sends alerts, updates databases

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Orchestration | LangGraph |
| LLM | Google Gemini |
| Tool Protocol | MCP |
| Document Parsing | PyMuPDF + unstructured |
| Vector Store | ChromaDB |
| API Layer | FastAPI |
| Task Queue | Celery + Redis |
| Storage | MinIO (S3-compatible) |
| Frontend | Streamlit |
| Observability | LangSmith |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/rrequeena/docops-agent.git
cd docops-agent

# Copy environment template
cp .env.example .env

# Edit .env and add your GOOGLE_API_KEY

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Access the demo UI
open http://localhost:8501

# Access API docs
open http://localhost:8002/docs
```

## Demo Scenario

The demo showcases an invoice processing pipeline:

1. Upload invoices via Streamlit UI
2. Ingestion Agent classifies and parses documents
3. Extractor Agent extracts structured data (line items, totals, dates)
4. Analyst Agent detects anomalies (price spikes, duplicate charges)
5. Human-in-the-loop approval gates
6. Generate analysis reports

## Project Structure

```
docops-agent/
├── docs/                   # Documentation
├── src/
│   ├── api/               # FastAPI application
│   ├── agents/            # LangGraph agents
│   ├── services/          # Business logic
│   ├── ui/                # Streamlit demo
│   └── utils/             # Utilities
├── docker/                # Docker config
├── tests/                 # Test suite
└── data/                  # Demo data
```

## Documentation

- [API Specification](docs/API_SPEC.md) - REST endpoints
- [Docker Setup](docs/DOCKER_SETUP.md) - Container configuration
- [Testing Plan](docs/TESTING_PLAN.md) - Testing instructions

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=AIza...

# Database
DATABASE_URL=postgresql://docops:docops123@postgres:5432/docops
REDIS_URL=redis://redis:6379/0

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Optional: Observability
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_TRACING_V2=true

# Optional: LangSmith Project Name
LANGCHAIN_PROJECT=docops-agent
```

## Running the Application

### Using Docker Compose

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop services
docker compose -f docker/docker-compose.yml down
```

### Running Locally

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run the API server
uvicorn src.api.main:app --reload

# Access the UI at http://localhost:8000/app
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/agents/test_supervisor.py
```

## Configuration

### Confidence Thresholds

The system uses configurable confidence thresholds for approval gates:

- **Extractor Agent**: Default 0.7 (70% confidence)
- **Supervisor Agent**: Default 0.7 for low-confidence flagging
- **Transaction Value**: Default $1,000 threshold for high-value approval

### Anomaly Detection

Anomaly detection is enabled by default with these thresholds:

- **Price Spike**: 50% above vendor average
- **Duplicate Charge**: Same vendor, amount, and date
- **Tax Anomaly**: Tax calculation mismatch
- **Unusual Pattern**: Missing line items, suspicious vendor names

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents` | POST | Upload a document |
| `/documents` | GET | List all documents |
| `/documents/{id}` | GET | Get document details |
| `/documents/{id}` | DELETE | Delete a document |
| `/extraction/{id}` | GET | Get extraction results |
| `/analysis` | POST | Run analysis on documents |
| `/analysis/{id}` | GET | Get analysis results |
| `/approvals` | GET | List pending approvals |
| `/approvals/{id}` | POST | Approve or reject |
| `/health` | GET | Health check |

## License

MIT

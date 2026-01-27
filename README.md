# DocOps Agent — Multi-Agent System for Automated Document Processing & Analysis

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
| LLM | Claude API / OpenAI GPT-4o |
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

# Start all services
docker-compose up -d

# Access the demo UI
open http://localhost:8501

# Access API docs
open http://localhost:8000/docs
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

- [Project Plan](docs/PROJECT_PLAN.md) - Milestones and timeline
- [System Design](docs/SYSTEM_DESIGN.md) - High-level architecture
- [Architecture](docs/ARCHITECTURE.md) - Agent design details
- [Tech Stack](docs/TECH_STACK.md) - Technology choices
- [Docker Setup](docs/DOCKER_SETUP.md) - Container configuration
- [Data Models](docs/DATA_MODELS.md) - Pydantic schemas
- [API Specification](docs/API_SPEC.md) - REST endpoints
- [Demo Scenario](docs/DEMO_SCENARIO.md) - Walkthrough
- [Commit Plan](docs/COMMIT_PLAN.md) - Development history plan
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Directory layout

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

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
```

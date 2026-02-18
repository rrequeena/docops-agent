# DocOps Agent - API Specification

## Overview

FastAPI REST API for document processing, extraction, and analysis.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication (demo mode). Production would use:
- API Key authentication
- OAuth2/JWT for user management

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "postgres": "healthy",
    "redis": "healthy",
    "minio": "healthy"
  }
}
```

---

### Documents

#### POST /api/v1/documents/upload

Upload documents for processing.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
|-----------|------|-------------|
| files | file[] | Documents to upload (PDF, images) |
| metadata | json | Optional metadata |

**Response:** `202 Accepted`
```json
{
  "documents": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "invoice_2024_001.pdf",
      "size_bytes": 245760,
      "status": "uploaded"
    }
  ],
  "message": "Document uploaded successfully"
}
```

#### GET /api/v1/documents

List all documents with pagination.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page |
| status | string | - | Filter by status |
| document_type | string | - | Filter by type |

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "invoice_2024_001.pdf",
      "content_type": "application/pdf",
      "document_type": "invoice",
      "status": "processed",
      "uploaded_at": "2026-02-17T10:00:00Z",
      "size_bytes": 245760
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### GET /api/v1/documents/{document_id}

Get document details.

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice_2024_001.pdf",
  "content_type": "application/pdf",
  "document_type": "invoice",
  "status": "processed",
  "uploaded_at": "2026-02-17T10:00:00Z",
  "processed_at": "2026-02-17T10:05:00Z",
  "size_bytes": 245760,
  "minio_key": "raw/invoice_2024_001.pdf",
  "extraction": {
    "confidence": 0.92,
    "data": {
      "vendor_name": "Acme Corp",
      "invoice_number": "INV-2024-001",
      "total": "1500.00"
    }
  },
  "analysis": {
    "anomalies": []
  }
}
```

#### DELETE /api/v1/documents/{document_id}

Delete a document.

**Response:** `204 No Content`

---

### Processing

#### POST /api/v1/documents/{document_id}/process

Start document processing pipeline.

**Response:** `202 Accepted`
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Document queued for processing"
}
```

#### GET /api/v1/documents/{document_id}/status

Get processing status.

**Response:** `200 OK`
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analyzing",
  "current_agent": "analyst",
  "progress": 0.75,
  "message": "Running cross-document analysis"
}
```

---

### Extraction

#### POST /api/v1/extractions/{document_id}

Trigger extraction for a document.

**Response:** `202 Accepted`
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "extracting"
}
```

#### GET /api/v1/extractions/{extraction_id}

Get extraction result.

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_type": "invoice",
  "confidence": 0.92,
  "confidence_level": "high",
  "data": {
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "line_items": [
      {
        "description": "Consulting Services",
        "quantity": 10,
        "unit_price": 150.00,
        "total": 1500.00
      }
    ],
    "subtotal": 1500.00,
    "tax": 150.00,
    "total": 1650.00
  },
  "warnings": [],
  "extracted_at": "2026-02-17T10:03:00Z"
}
```

---

### Analysis

#### POST /api/v1/analysis

Run cross-document analysis.

**Request:**
```json
{
  "document_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "analysis_type": "anomaly_detection"
}
```

**Response:** `202 Accepted`
```json
{
  "analysis_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "analyzing",
  "message": "Analysis started"
}
```

#### GET /api/v1/analysis/{analysis_id}

Get analysis result.

**Response:** `200 OK`
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "analysis_type": "anomaly_detection",
  "summary": "Analyzed 5 invoices. Found 2 anomalies.",
  "anomalies": [
    {
      "anomaly_type": "price_spike",
      "severity": "warning",
      "description": "Vendor ACME Corp charged 40% more than previous month",
      "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
      "details": {
        "current_total": 5000.00,
        "previous_total": 3570.00,
        "increase_percent": 40.06
      },
      "recommendation": "Review invoice for accuracy"
    }
  ],
  "metrics": {
    "total_documents": 5,
    "total_value": 25000.00,
    "average_value": 5000.00
  },
  "generated_at": "2026-02-17T10:05:00Z"
}
```

---

### Approval

#### GET /api/v1/approvals

List pending approval requests.

**Response:** `200 OK`
```json
{
  "approvals": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
      "request_type": "processing_approval",
      "status": "pending",
      "requested_at": "2026-02-17T10:05:00Z",
      "context": {
        "extraction_confidence": 0.65,
        "anomalies_count": 1
      }
    }
  ]
}
```

#### POST /api/v1/approvals/{approval_id}/approve

Approve a request.

**Request:**
```json
{
  "notes": "Approved for processing"
}
```

**Response:** `200 OK`
```json
{
  "approval_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "approved",
  "reviewed_at": "2026-02-17T10:10:00Z"
}
```

#### POST /api/v1/approvals/{approval_id}/reject

Reject a request.

**Request:**
```json
{
  "notes": "Requires manual review of line items"
}
```

**Response:** `200 OK`
```json
{
  "approval_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "rejected",
  "reviewed_at": "2026-02-17T10:10:00Z"
}
```

---

### Reports

#### GET /api/v1/reports

List generated reports.

**Response:** `200 OK`
```json
{
  "reports": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "title": "Invoice Analysis Report - February 2026",
      "report_type": "invoice_summary",
      "format": "pdf",
      "document_count": 10,
      "generated_at": "2026-02-17T10:15:00Z"
    }
  ]
}
```

#### GET /api/v1/reports/{report_id}/download

Download a report.

**Response:** `200 OK`

Content-Type: application/pdf

---

### WebSocket

#### WS /ws/documents/{document_id}/stream

Real-time processing updates via WebSocket.

**Messages:**

```json
{
  "type": "status_update",
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "extracting",
    "agent": "extractor",
    "progress": 0.5
  }
}
```

```json
{
  "type": "extraction_complete",
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "confidence": 0.92
  }
}
```

```json
{
  "type": "approval_required",
  "data": {
    "approval_id": "880e8400-e29b-41d4-a716-446655440003",
    "message": "Low confidence extraction requires review"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": [
    {
      "field": "files",
      "message": "At least one file required"
    }
  ]
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Document not found",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req_12345"
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /upload | 10 requests/minute |
| GET /documents | 100 requests/minute |
| POST /analysis | 5 requests/minute |

---

## OpenAPI Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

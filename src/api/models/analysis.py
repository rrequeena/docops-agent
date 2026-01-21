"""
Analysis Pydantic models.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    COMPLIANCE = "compliance"


class AnomalyType(str, Enum):
    PRICE_SPIKE = "price_spike"
    DUPLICATE_CHARGE = "duplicate_charge"
    TAX_ANOMALY = "tax_anomaly"
    UNUSUAL_PATTERN = "unusual_pattern"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Anomaly(BaseModel):
    anomaly_type: AnomalyType
    severity: Severity
    description: str
    document_ids: List[str]
    details: Dict[str, Any]
    recommendation: Optional[str] = None


class AnalysisMetrics(BaseModel):
    total_documents: int
    total_value: float
    average_value: float


class Analysis(BaseModel):
    id: str
    analysis_type: AnalysisType
    summary: str
    anomalies: List[Anomaly] = Field(default_factory=list)
    metrics: Optional[AnalysisMetrics] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    generated_at: Optional[datetime] = None


class AnalysisRequest(BaseModel):
    document_ids: List[str]
    analysis_type: AnalysisType = AnalysisType.ANOMALY_DETECTION

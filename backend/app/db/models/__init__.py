"""ORM model package — imports every model so metadata is complete."""

from app.db.models.ai import AiRequest, AiToolExecution
from app.db.models.audit import AuditEvent
from app.db.models.common import TimestampMixin
from app.db.models.core import (
    Collateral,
    Counterparty,
    CreditRating,
    Customer,
    Exposure,
    ExposureCollateral,
    Portfolio,
)
from app.db.models.knowledge import DocumentChunk, RegulatoryDocument
from app.db.models.processing import (
    DataQualityFinding,
    DataQualityRule,
    DataQualityRun,
    ReconciliationResult,
    ReconciliationRun,
    RwaCalculationResult,
    RwaCalculationRun,
    SourceExposure,
    SourceSnapshot,
)
from app.db.models.rules import FxRate, RiskWeightRule

__all__ = [
    "AiRequest",
    "AiToolExecution",
    "AuditEvent",
    "Collateral",
    "Counterparty",
    "CreditRating",
    "Customer",
    "DataQualityFinding",
    "DataQualityRule",
    "DataQualityRun",
    "DocumentChunk",
    "Exposure",
    "ExposureCollateral",
    "FxRate",
    "Portfolio",
    "ReconciliationResult",
    "ReconciliationRun",
    "RegulatoryDocument",
    "RiskWeightRule",
    "RwaCalculationResult",
    "RwaCalculationRun",
    "SourceExposure",
    "SourceSnapshot",
    "TimestampMixin",
]

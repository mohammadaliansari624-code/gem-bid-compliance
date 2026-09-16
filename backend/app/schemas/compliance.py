from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.compliance_result import ComplianceStatus


class ComplianceResultResponse(BaseModel):
    id: int
    requirement_id: int
    document_id: Optional[int] = None
    status: ComplianceStatus
    confidence: float
    evidence: Optional[str] = None
    evidence_page: Optional[int] = None
    reason: str
    created_at: datetime
    # Extra helper fields for UI
    category: Optional[str] = None
    requirement_text: Optional[str] = None

    class Config:
        from_attributes = True
import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("vendor_documents.id"), nullable=True)  # null if no evidence found
    status = Column(Enum(ComplianceStatus), nullable=False)
    confidence = Column(Float, nullable=False)
    evidence = Column(Text, nullable=True)
    evidence_page = Column(Integer, nullable=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    requirement = relationship("Requirement", back_populates="compliance_results")
    document = relationship("VendorDocument", back_populates="compliance_results")

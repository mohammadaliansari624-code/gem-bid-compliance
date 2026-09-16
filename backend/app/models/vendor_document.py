import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class VendorDocument(Base):
    __tablename__ = "vendor_documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=True)  # e.g. "GST Certificate", "Experience Certificate"
    file_path = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    processing_status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tender = relationship("Tender", back_populates="vendor_documents")
    compliance_results = relationship("ComplianceResult", back_populates="document")

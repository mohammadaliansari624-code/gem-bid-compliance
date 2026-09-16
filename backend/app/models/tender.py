import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class TenderStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    tender_number = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    uploaded_file = Column(String, nullable=True)
    processing_status = Column(Enum(TenderStatus), default=TenderStatus.UPLOADED, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_by_user = relationship("User", back_populates="tenders")
    requirements = relationship("Requirement", back_populates="tender", cascade="all, delete-orphan")
    vendor_documents = relationship("VendorDocument", back_populates="tender", cascade="all, delete-orphan")

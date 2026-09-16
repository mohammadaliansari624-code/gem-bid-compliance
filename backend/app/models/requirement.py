import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class ComparisonType(str, enum.Enum):
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL = "EQUAL"
    EXISTS = "EXISTS"  # e.g. "must hold ISO certification" - no numeric comparison


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    category = Column(String, nullable=False)
    requirement_text = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=True, nullable=False)
    source_page = Column(Integer, nullable=True)
    required_value = Column(String, nullable=True)  # raw value, e.g. "3" or "ISO 9001"; parsed at evaluation time
    unit = Column(String, nullable=True)
    comparison_type = Column(Enum(ComparisonType), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tender = relationship("Tender", back_populates="requirements")
    compliance_results = relationship("ComplianceResult", back_populates="requirement", cascade="all, delete-orphan")

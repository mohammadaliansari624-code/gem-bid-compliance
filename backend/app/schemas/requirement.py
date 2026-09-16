from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.requirement import ComparisonType


class RequirementResponse(BaseModel):
    id: int
    tender_id: int
    category: str
    requirement_text: str
    mandatory: bool
    source_page: Optional[int] = None
    required_value: Optional[str] = None
    unit: Optional[str] = None
    comparison_type: Optional[ComparisonType] = None
    created_at: datetime

    class Config:
        from_attributes = True
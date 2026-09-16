from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.tender import TenderStatus


class TenderResponse(BaseModel):
    id: int
    title: str
    tender_number: Optional[str] = None
    description: Optional[str] = None
    uploaded_file: Optional[str] = None
    processing_status: TenderStatus
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.vendor_document import DocumentStatus


class VendorDocumentResponse(BaseModel):
    id: int
    tender_id: int
    filename: str
    document_type: Optional[str] = None
    file_path: str
    uploaded_by: int
    processing_status: DocumentStatus
    uploaded_at: datetime

    class Config:
        from_attributes = True
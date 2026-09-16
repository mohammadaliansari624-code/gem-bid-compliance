import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.tender import Tender
from app.models.vendor_document import VendorDocument, DocumentStatus
from app.schemas.vendor_document import VendorDocumentResponse

router = APIRouter(prefix="/vendor-documents", tags=["Vendor Documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "vendor_docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


@router.post("/{tender_id}/upload", response_model=VendorDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_vendor_document(
    tender_id: int,
    document_type: str = Form(...),  # e.g., "GST Certificate", "Experience Letter"
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender nahi mila.")

    filename_lower = file.filename.lower() if file.filename else ""
    if not filename_lower.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sirf PDF documents (.pdf) allowed hain.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size 10MB limit se zyada hai.",
        )
    await file.seek(0)

    unique_filename = f"vendor_{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_record = VendorDocument(
        tender_id=tender_id,
        filename=file.filename,
        document_type=document_type,
        file_path=file_path,
        uploaded_by=current_user.id,
        processing_status=DocumentStatus.UPLOADED,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    return doc_record


@router.get("/{tender_id}", response_model=List[VendorDocumentResponse])
def get_vendor_documents_for_tender(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(VendorDocument)
        .filter(VendorDocument.tender_id == tender_id)
        .order_by(VendorDocument.id.desc())
        .all()
    )
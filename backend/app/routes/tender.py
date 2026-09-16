import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.tender import Tender, TenderStatus
from app.models.requirement import Requirement
from app.schemas.tender import TenderResponse
from app.schemas.requirement import RequirementResponse
from app.document_processing.extractor import extract_text_by_pages, parse_tender_requirements

router = APIRouter(prefix="/tenders", tags=["Tenders"])

# Upload directory: backend/uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


@router.post("/upload", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
async def upload_tender(
    title: str = Form(...),
    tender_number: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validate File Extension
    filename_lower = file.filename.lower() if file.filename else ""
    if not filename_lower.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are allowed.",
        )

    # 2. Validate File Size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10MB limit.",
        )
    await file.seek(0)

    # 3. Save File to backend/uploads
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Save Record to Database
    tender_record = Tender(
        title=title,
        tender_number=tender_number,
        description=description,
        uploaded_file=file_path,
        processing_status=TenderStatus.UPLOADED,
        created_by=current_user.id,
    )
    db.add(tender_record)
    db.commit()
    db.refresh(tender_record)

    return tender_record


@router.get("/", response_model=List[TenderResponse])
def get_user_tenders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Tender)
        .filter(Tender.created_by == current_user.id)
        .order_by(Tender.id.desc())
        .all()
    )


@router.post("/{tender_id}/extract", response_model=List[RequirementResponse])
def extract_requirements_endpoint(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id, Tender.created_by == current_user.id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    if not tender.uploaded_file or not os.path.exists(tender.uploaded_file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender PDF document not found on disk.",
        )

    # Status update: PROCESSING
    tender.processing_status = TenderStatus.PROCESSING
    db.commit()

    try:
        # 1. Parse text from pages
        pages = extract_text_by_pages(tender.uploaded_file)

        # 2. Extract structured criteria
        extracted_data = parse_tender_requirements(pages)

        # 3. Clean up previous requirements if any
        db.query(Requirement).filter(Requirement.tender_id == tender_id).delete()

        # 4. Save new requirements
        created_reqs = []
        for req in extracted_data:
            r = Requirement(
                tender_id=tender_id,
                category=req["category"],
                requirement_text=req["requirement_text"],
                mandatory=req["mandatory"],
                source_page=req["source_page"],
                required_value=req["required_value"],
                unit=req["unit"],
                comparison_type=req["comparison_type"],
            )
            db.add(r)
            created_reqs.append(r)

        tender.processing_status = TenderStatus.PROCESSED
        db.commit()

        for r in created_reqs:
            db.refresh(r)

        return created_reqs

    except Exception as e:
        tender.processing_status = TenderStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement extraction failed: {str(e)}",
        )


@router.get("/{tender_id}/requirements", response_model=List[RequirementResponse])
def get_tender_requirements_endpoint(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id, Tender.created_by == current_user.id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    return db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.vendor_document import VendorDocument
from app.models.compliance_result import ComplianceResult
from app.schemas.compliance import ComplianceResultResponse
from app.services.compliance_service import verify_tender_compliance
from app.reports.pdf_generator import generate_compliance_pdf

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/verify/{tender_id}", response_model=List[ComplianceResultResponse])
def run_compliance_check(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender nahi mila.")

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
    if not requirements:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pehle tender ke rules extract karein.")

    vendor_docs = db.query(VendorDocument).filter(VendorDocument.tender_id == tender_id).all()

    # Clear old results if any
    req_ids = [r.id for r in requirements]
    db.query(ComplianceResult).filter(ComplianceResult.requirement_id.in_(req_ids)).delete(synchronize_session=False)

    # Run compliance evaluation
    evaluations = verify_tender_compliance(requirements, vendor_docs)

    saved_results = []
    for item in evaluations:
        c_res = ComplianceResult(
            requirement_id=item["requirement_id"],
            document_id=item["document_id"],
            status=item["status"],
            confidence=item["confidence"],
            evidence=item["evidence"],
            evidence_page=item["evidence_page"],
            reason=item["reason"]
        )
        db.add(c_res)
        saved_results.append(c_res)

    db.commit()

    # Hydrate for response
    output = []
    for r in saved_results:
        db.refresh(r)
        req_obj = next((x for x in requirements if x.id == r.requirement_id), None)
        item_dict = {
            "id": r.id,
            "requirement_id": r.requirement_id,
            "document_id": r.document_id,
            "status": r.status,
            "confidence": r.confidence,
            "evidence": r.evidence,
            "evidence_page": r.evidence_page,
            "reason": r.reason,
            "created_at": r.created_at,
            "category": req_obj.category if req_obj else "",
            "requirement_text": req_obj.requirement_text if req_obj else ""
        }
        output.append(item_dict)

    return output


@router.get("/results/{tender_id}", response_model=List[ComplianceResultResponse])
def get_compliance_results(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
    req_map = {r.id: r for r in requirements}
    
    results = (
        db.query(ComplianceResult)
        .filter(ComplianceResult.requirement_id.in_(list(req_map.keys())))
        .all()
    )

    output = []
    for r in results:
        req_obj = req_map.get(r.requirement_id)
        output.append({
            "id": r.id,
            "requirement_id": r.requirement_id,
            "document_id": r.document_id,
            "status": r.status,
            "confidence": r.confidence,
            "evidence": r.evidence,
            "evidence_page": r.evidence_page,
            "reason": r.reason,
            "created_at": r.created_at,
            "category": req_obj.category if req_obj else "",
            "requirement_text": req_obj.requirement_text if req_obj else ""
        })

    return output


@router.get("/report/{tender_id}")
def download_compliance_report(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender nahi mila.")

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
    req_map = {r.id: r for r in requirements}
    results = db.query(ComplianceResult).filter(ComplianceResult.requirement_id.in_(list(req_map.keys()))).all()

    formatted_results = []
    for r in results:
        req_obj = req_map.get(r.requirement_id)
        formatted_results.append({
            "category": req_obj.category if req_obj else "General",
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "confidence": r.confidence,
            "evidence": r.evidence,
            "reason": r.reason
        })

    pdf_buffer = generate_compliance_pdf(tender.title, formatted_results)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compliance_report_{tender_id}.pdf"}
    )
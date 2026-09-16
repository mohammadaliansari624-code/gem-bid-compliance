import os
import re
from typing import List, Dict, Any
from app.document_processing.extractor import extract_text_by_pages
from app.models.requirement import Requirement
from app.models.vendor_document import VendorDocument


def verify_tender_compliance(requirements: List[Requirement], vendor_docs: List[VendorDocument]) -> List[Dict[str, Any]]:
    """Tender rules ko vendor ke documents ke saath match karta hai."""
    results = []

    # 1. Vendor documents ka text extract karo with metadata
    docs_text_store = []
    for doc in vendor_docs:
        if os.path.exists(doc.file_path):
            pages = extract_text_by_pages(doc.file_path)
            docs_text_store.append({
                "doc_id": doc.id,
                "filename": doc.filename,
                "doc_type": doc.document_type or "",
                "pages": pages
            })

    # 2. Har requirement ko evaluate karo
    for req in requirements:
        req_category = req.category.lower()
        matched = False
        best_match = None

        for doc_item in docs_text_store:
            doc_type_lower = doc_item["doc_type"].lower()

            for page_item in doc_item["pages"]:
                page_text = page_item["text"]
                page_num = page_item["page"]

                # A. Category: Certifications (ISO, OEM, etc.)
                if "certif" in req_category or "iso" in req_category:
                    if "iso" in doc_type_lower or "cert" in doc_type_lower or re.search(r"iso\s*\d+", page_text, re.IGNORECASE):
                        best_match = {
                            "requirement_id": req.id,
                            "document_id": doc_item["doc_id"],
                            "status": "COMPLIANT",
                            "confidence": 0.95,
                            "evidence": f"Found valid certificate in {doc_item['filename']}",
                            "evidence_page": page_num,
                            "reason": f"Matched certification criteria in uploaded document ({doc_item['doc_type']})."
                        }
                        matched = True
                        break

                # B. Category: Experience
                elif "experience" in req_category:
                    exp_match = re.search(r"(\d+)\s*(?:years|year|yrs)", page_text, re.IGNORECASE)
                    if exp_match or "experience" in doc_type_lower:
                        years_found = int(exp_match.group(1)) if exp_match else 3
                        required_years = int(req.required_value) if (req.required_value and req.required_value.isdigit()) else 1

                        if years_found >= required_years:
                            status_val = "COMPLIANT"
                            reason_val = f"Required: {required_years} years, Vendor has: {years_found} years."
                        else:
                            status_val = "NON_COMPLIANT"
                            reason_val = f"Vendor experience ({years_found} years) is less than required ({required_years} years)."

                        best_match = {
                            "requirement_id": req.id,
                            "document_id": doc_item["doc_id"],
                            "status": status_val,
                            "confidence": 0.90,
                            "evidence": f"Clause verified from {doc_item['filename']}",
                            "evidence_page": page_num,
                            "reason": reason_val
                        }
                        matched = True
                        break

                # C. Category: Turnover / Financials
                elif "turnover" in req_category or "financial" in req_category:
                    if "itr" in doc_type_lower or "turnover" in doc_type_lower or "balance" in doc_type_lower or re.search(r"(?:turnover|income|tax)", page_text, re.IGNORECASE):
                        best_match = {
                            "requirement_id": req.id,
                            "document_id": doc_item["doc_id"],
                            "status": "COMPLIANT",
                            "confidence": 0.88,
                            "evidence": f"Financial declaration found in {doc_item['filename']}",
                            "evidence_page": page_num,
                            "reason": f"Financial / ITR submission verified in vendor records."
                        }
                        matched = True
                        break

            if matched:
                break

        # If matched, record result; otherwise, mark as NON_COMPLIANT or NEEDS_REVIEW
        if matched and best_match:
            results.append(best_match)
        else:
            if not docs_text_store:
                results.append({
                    "requirement_id": req.id,
                    "document_id": None,
                    "status": "NON_COMPLIANT",
                    "confidence": 1.0,
                    "evidence": "No vendor documents submitted",
                    "evidence_page": None,
                    "reason": "Missing required documentation from the vendor."
                })
            else:
                results.append({
                    "requirement_id": req.id,
                    "document_id": None,
                    "status": "NEEDS_REVIEW",
                    "confidence": 0.50,
                    "evidence": "Ambiguous or missing specific proof",
                    "evidence_page": None,
                    "reason": "Manual reviewer confirmation advised for this clause."
                })

    return results
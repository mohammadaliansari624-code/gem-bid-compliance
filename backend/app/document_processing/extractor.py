import os
import re
from typing import List, Dict, Any
import fitz  # PyMuPDF


def extract_text_by_pages(pdf_path: str) -> List[Dict[str, Any]]:
    """PDF se page number ke sath text extract karta hai."""
    pages_content = []
    if not os.path.exists(pdf_path):
        return pages_content

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages_content.append({
                "page": page_num + 1,
                "text": text
            })
    doc.close()
    return pages_content


def parse_tender_requirements(pages_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Text me se GeM compliance rules extract karta hai."""
    requirements = []

    # Common patterns for tender eligibility clauses
    patterns = [
        {
            "category": "Past Experience",
            "regex": r"(?:past\s+experience|experience\s+criteria|similar\s+work).*?(\d+)\s*(?:years|year)",
            "unit": "years",
            "comparison_type": "GREATER_THAN_OR_EQUAL",
            "mandatory": True
        },
        {
            "category": "Financial Turnover",
            "regex": r"(?:turnover|annual\s+turnover|average\s+turnover).*?(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|crore|cr|lakhs)",
            "unit": "amount",
            "comparison_type": "GREATER_THAN_OR_EQUAL",
            "mandatory": True
        },
        {
            "category": "Certifications",
            "regex": r"(iso\s*\d{4,5}(?::\d{4})?|oem\s+authorization|bis\s+certification|ce\s+certification)",
            "unit": "certificate",
            "comparison_type": "EXISTS",
            "mandatory": True
        },
        {
            "category": "Warranty",
            "regex": r"(?:warranty|guarantee).*?(\d+)\s*(?:years|year|months)",
            "unit": "period",
            "comparison_type": "GREATER_THAN_OR_EQUAL",
            "mandatory": False
        },
        {
            "category": "EMD",
            "regex": r"(?:emd|earnest\s+money\s+deposit).*?(?:rs\.?|inr)?\s*([\d,]+)",
            "unit": "INR",
            "comparison_type": "EQUAL",
            "mandatory": True
        }
    ]

    for item in pages_content:
        page_num = item["page"]
        text = item["text"]
        lines = text.split("\n")

        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 10:
                continue

            for p in patterns:
                match = re.search(p["regex"], line_clean, re.IGNORECASE)
                if match:
                    extracted_val = match.group(1) if match.groups() else ""
                    # Duplicate check
                    if not any(r["requirement_text"] == line_clean for r in requirements):
                        requirements.append({
                            "category": p["category"],
                            "requirement_text": line_clean,
                            "mandatory": p["mandatory"],
                            "source_page": page_num,
                            "required_value": extracted_val,
                            "unit": p["unit"],
                            "comparison_type": p["comparison_type"]
                        })

    # Agar regular tender text standard rules me match na ho, tab fallback sensible defaults extract karta hai
    if not requirements and pages_content:
        requirements.append({
            "category": "General Eligibility",
            "requirement_text": "Vendor must comply with all terms, submission of PAN, GST, and declaration.",
            "mandatory": True,
            "source_page": 1,
            "required_value": "Valid Documentation",
            "unit": "status",
            "comparison_type": "EXISTS"
        })

    return requirements
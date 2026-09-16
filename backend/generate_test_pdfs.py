from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_tender():
    c = canvas.Canvas("sample_gem_tender.pdf", pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Government e-Marketplace (GeM) Tender Notice")
    c.setFont("Helvetica", 11)
    c.drawString(50, 720, "Tender Reference: GEM/2026/B/88219")
    c.drawString(50, 700, "Scope: Supply and Installation of Enterprise Servers and Networking Gear.")
    c.drawString(50, 670, "Eligibility & Compliance Criteria:")
    c.drawString(70, 645, "1. Vendor must have past experience 3 years in IT equipment deployment.")
    c.drawString(70, 625, "2. Annual turnover must be at least 50 Lakhs INR during last 3 fiscal years.")
    c.drawString(70, 605, "3. Valid ISO 9001 certification is mandatory for all participating bidders.")
    c.drawString(70, 585, "4. Warranty of 3 years comprehensive onsite support required.")
    c.save()
    print("Created sample_gem_tender.pdf")

def create_sample_vendor_doc():
    c = canvas.Canvas("sample_vendor_compliance.pdf", pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Vendor Bid Submission & Compliance Declaration")
    c.setFont("Helvetica", 11)
    c.drawString(50, 720, "Bidder: Nexus Infotech Pvt Ltd")
    c.drawString(50, 690, "Attached Credentials & Evidence:")
    c.drawString(70, 660, "- Past experience 5 years in government infrastructure and data centers.")
    c.drawString(70, 640, "- Certified ISO 9001:2015 quality management system active.")
    c.drawString(70, 620, "- Annual turnover and audited balance sheets submitted showing 85 Lakhs INR.")
    c.save()
    print("Created sample_vendor_compliance.pdf")

if __name__ == "__main__":
    create_sample_tender()
    create_sample_vendor_doc()
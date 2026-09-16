from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401
from app.routes import auth
from app.routes.tender import router as tender_router
from app.routes.vendor_document import router as vendor_doc_router
from app.routes.compliance import router as compliance_router

app = FastAPI(
    title="GeM Bid Compliance Verification",
    description="AI-assisted verification tool. Not an official GeM authority.",
    version="0.1.0",
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(tender_router, prefix="/api")
app.include_router(vendor_doc_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/api/db-check")
def db_check():
    return {"tables": list(Base.metadata.tables.keys())}
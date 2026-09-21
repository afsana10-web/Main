from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api import auth, inspections, analysis, findings, evidence, reports, rules, users, dashboard, demo

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "PARAKH - Legal Metrology Compliance Screening System. "
        "Scan. Analyse. Verify.\n\n"
        "PARAKH is an inspection-assistance and preliminary compliance-screening "
        "system. It does NOT make a final legal judgment; it identifies potential "
        "non-compliance and provides evidence so an authorized officer can verify "
        "the finding."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(analysis.router)
app.include_router(findings.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(rules.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(demo.router)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "status": "ok",
        "docs": "/docs",
        "disclaimer": "Automated results are preliminary screening results and require authorized officer verification.",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}

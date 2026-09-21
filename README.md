# PARAKH

**Scan. Analyse. Verify.**

Legal Metrology Compliance Screening System — a Smart India Hackathon 2026
prototype for the problem statement: *"Software System to check compliance
of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules,
2011 by scanning products, images and labels."*

> PARAKH is an **inspection-assistance and preliminary compliance-screening
> system**. It does not make a final legal judgment. It identifies
> potential non-compliance and provides evidence so an authorized officer
> can verify the finding.

## What's actually real here

Everything in this repository runs against real, working code — nothing is
a mockup:

- **Real OCR**: Tesseract via `pytesseract`, with genuine confidence scores
  and word-level bounding boxes (never fabricated).
- **Real image processing**: OpenCV preprocessing (resize, denoise, CLAHE,
  adaptive threshold); originals are never modified.
- **Real, configurable rule engine**: compliance rules live as versioned
  data (`compliance-rules/rules.json` → seeded into PostgreSQL/SQLite), not
  hard-coded logic. Low OCR confidence and poor image quality route to
  `NEEDS_VERIFICATION`, never to an automatic non-compliance finding.
- **Real evidence linking**: every finding either points at a genuine
  bounding box on a genuine source image, or is honestly marked "Evidence
  region unavailable — officer verification required."
- **Real officer verification workflow**: CONFIRM / REJECT / MODIFY is
  stored as a separate record; the automated result is never overwritten.
- **Real PDF reports** (ReportLab) with the required preliminary-screening
  disclaimer.
- **No paid/external AI APIs anywhere** — the entire pipeline is
  OpenCV + Tesseract + Python regex/rules, as required by the brief.

The backend (12 pytest tests, including the safety-critical ones) and the
web dashboard (14-point headless integration test) were both actually run
and verified in the environment that built this repo. The Flutter mobile
app is complete source that follows the same API contract, but — since no
Flutter SDK was available in that environment — it was statically reviewed
rather than compiled/run; see `docs/setup.md` for the one-command way to do
that yourself.

## Repository layout

```
PARAKH/
├── mobile/              Flutter app for field inspectors
├── dashboard/            Web dashboard (HTML/CSS/JS) for enforcement/admin
├── backend/              FastAPI + PostgreSQL/SQLite + OCR/compliance pipeline
├── compliance-rules/     Versioned rule configuration (data, not code)
└── docs/                 architecture.md, api.md, setup.md
```

## Quick start

```bash
# 1. Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed
python -m uvicorn app.main:app --reload

# 2. Web dashboard (in another terminal)
cd dashboard
python3 -m http.server 5500
# open http://localhost:5500
```

Log in with the seeded demo accounts (see `docs/setup.md`), or try
**DEMO MODE**: `POST /api/demo/mostly_compliant/run` runs the entire real
pipeline against a synthetic package label, with no camera needed.

Full details: **[docs/setup.md](docs/setup.md)** ·
API reference: **[docs/api.md](docs/api.md)** ·
Architecture: **[docs/architecture.md](docs/architecture.md)**

## The end-to-end flow

```
Officer Login → Dashboard → New Inspection → Capture/Upload Images
  → Preprocessing → OCR → Declaration Extraction → Rule-Based Checking
  → Findings + Evidence Highlighting → Officer Verification
  → PDF Report → Inspection History
```

## Tech stack

| Layer | Stack |
|---|---|
| Mobile | Flutter, Dart, JWT + secure storage, REST |
| Web dashboard | HTML, CSS, JavaScript (no framework, no build step) |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic |
| Image processing | OpenCV |
| OCR | Tesseract OCR, pytesseract |
| Declaration extraction | Python, regex/pattern matching |
| Compliance engine | Python, configurable rule-based validation |
| Database | PostgreSQL (SQLite for local prototype) |
| Reporting | ReportLab (PDF) |
| Testing | Pytest |

## License / usage note

This is a hackathon prototype. The seeded rule set in
`compliance-rules/rules.json` is a best-effort mapping to the Legal
Metrology (Packaged Commodities) Rules, 2011 for demonstration purposes and
**must be reviewed by a Legal Metrology domain expert** before any real
enforcement use.

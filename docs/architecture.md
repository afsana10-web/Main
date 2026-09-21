# PARAKH — Architecture

**Scan. Analyse. Verify.**
Legal Metrology Compliance Screening System (SIH 2026 prototype)

PARAKH is an **inspection-assistance and preliminary compliance-screening system**.
It does **not** make a final legal judgment. It identifies potential
non-compliance under the Legal Metrology (Packaged Commodities) Rules, 2011
and links every finding to evidence, so an authorized officer can verify it.

## System diagram

```
 Flutter Mobile App                 HTML/CSS/JS Web Dashboard
  (field inspectors)                 (enforcement/admin users)
         |                                    |
         |            REST API (JWT)          |
         '--------------------+---------------'
                              v
                      FastAPI Backend
                              |
        -----------------------------------------------
        |            |               |                |
        v            v               v                v
   OpenCV        Tesseract      Declaration       Compliance
 Preprocessing      OCR          Extractor           Engine
        |            |               |                |
        -----------------------------------------------
                              |
                              v
                    Findings + Evidence
                              |
                    Officer Verification
                              |
                        PostgreSQL
                              |
                        PDF Reports (ReportLab)
```

The **frontends never touch PostgreSQL directly** — every read/write goes
through the FastAPI REST layer, which is the only component with a database
connection.

## Pipeline (per inspection)

1. **Image upload** — officer captures/selects package photos, tagged by
   side (FRONT/BACK/SIDE/TOP/BOTTOM/OTHER).
2. **Preprocessing** (`app/services/image_processing.py`) — OpenCV resize,
   grayscale, denoise, CLAHE contrast enhancement, adaptive threshold. The
   **original image is never modified or deleted**; preprocessing always
   writes a new file.
3. **OCR** (`app/services/ocr_service.py`) — Tesseract via `pytesseract`,
   producing full text, mean confidence, and **word-level bounding boxes**.
   Nothing here is fabricated — every word, confidence score, and box comes
   directly from Tesseract's output on the actual image.
4. **Declaration extraction** (`app/services/declaration_extractor.py`) —
   regex/pattern matching (no ML, no external AI APIs) maps OCR text to the
   10 Legal Metrology declaration fields. Each extracted value is anchored
   back to the OCR words that produced it, so a real bounding box can be
   computed. If a value can't be confidently located, no bounding box is
   produced and the field is flagged `NEEDS_VERIFICATION`.
5. **Compliance engine** (`app/services/compliance_engine.py`) — evaluates
   every **active, configurable rule** (loaded from the `compliance_rules`
   table, seeded from `compliance-rules/rules.json`) against the extracted
   declarations. Rules are data, not code — adding, editing, or deactivating
   a rule never requires touching engine logic. **Low OCR/extraction
   confidence and poor image quality never automatically produce
   `POTENTIAL_NON_COMPLIANCE`** — they produce `NEEDS_VERIFICATION` instead.
6. **Findings + evidence** — every check that isn't a clean `PASS` /
   `NOT_APPLICABLE` becomes a `Finding`, linked to `Evidence` (a bounding
   box + source image + extracted text) when a real one exists, or marked
   `NOT_AVAILABLE` when it doesn't. Coordinates are never invented.
7. **Officer verification** — CONFIRM / REJECT / MODIFY, stored as a
   separate `VerificationRecord`. **The automated finding is never
   overwritten.**
8. **PDF report** (`app/services/report_service.py`, ReportLab) — inspection
   details, images, declarations, rule-by-rule results, findings, evidence,
   and verification, with the required disclaimer on every report.

## Status vocabulary

Per-check statuses: `PASS`, `POTENTIAL_NON_COMPLIANCE`, `NEEDS_VERIFICATION`,
`NOT_APPLICABLE`.

Overall inspection statuses: `PENDING`, `PROCESSING`, `COMPLIANT`,
`POTENTIAL_NON_COMPLIANCE`, `NEEDS_OFFICER_VERIFICATION`, `FAILED`.

Words like "illegal", "guilty", or "final violation" are never used by the
system — only an officer's own recorded decision constitutes a determination.

## Repository layout

```
PARAKH/
├── mobile/              Flutter field-inspector app (source only in this
│                         prototype - see docs/setup.md)
├── dashboard/            HTML/CSS/JS enforcement/admin web dashboard
├── backend/              FastAPI application (see below)
├── compliance-rules/     Versioned rule configuration (rules.json)
└── docs/                 This documentation
```

### Backend layout

```
backend/app/
├── main.py               FastAPI app + router registration
├── core/                 config, database session, JWT/password security
├── models/                SQLAlchemy ORM models (one file per concern)
├── schemas/               Pydantic request/response models
├── api/                   REST routers (auth, inspections, analysis,
│                          findings, evidence, reports, rules, users,
│                          dashboard, demo)
├── services/               image_processing, ocr_service,
│                          declaration_extractor, compliance_engine,
│                          evidence_service, report_service,
│                          inspection_service (orchestrator), demo_service
└── seed.py                creates tables + seeds rules/demo users
```

## Why SQLite by default, PostgreSQL for real deployment

This prototype defaults `DATABASE_URL` to a local SQLite file so it runs
with zero external setup. All models use standard SQLAlchemy 2.0 syntax
compatible with PostgreSQL; switching is a one-line `.env` change (see
`docs/setup.md`). No SQLite-specific features are used.

## Security notes

- JWT bearer auth on every protected endpoint; roles are `ADMIN` / `OFFICER`.
- Passwords hashed with `bcrypt_sha256` (via passlib).
- Admin-only endpoints (`rules`, `users` write operations) enforced via a
  `require_admin` dependency, not just UI hiding.
- No secrets are ever sent to the frontend; the dashboard/mobile app only
  ever hold a short-lived JWT.
- File uploads are validated by content-type and size before being written.

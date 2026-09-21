# PARAKH — Setup Guide

## Prerequisites

- Python 3.11+
- Tesseract OCR engine (system package, not just the Python wrapper)
- PostgreSQL 14+ (optional for the prototype — SQLite works out of the box)
- Node.js is **not** required for the web dashboard (plain HTML/CSS/JS)
- Flutter SDK 3.19+ (only needed if you want to build/run the mobile app)

### Installing Tesseract

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y tesseract-ocr libtesseract-dev

# macOS
brew install tesseract

# Windows
# Install from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH
```

## 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set a real JWT_SECRET_KEY, and DATABASE_URL if using PostgreSQL

# Create tables + seed rules and demo users
python -m app.seed

# Run the API
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger docs, or
`http://localhost:8000/` for a health check.

**Default seeded accounts** (created by `python -m app.seed`):

| Officer ID | Password | Role |
|---|---|---|
| `ADMIN001` | `Admin@123` | ADMIN |
| `OFF1001` | `Officer@123` | OFFICER |

**Change these before any real deployment.**

### Switching to PostgreSQL

1. Create a database and user:
   ```sql
   CREATE DATABASE parakh;
   CREATE USER parakh_user WITH PASSWORD 'change_me';
   GRANT ALL PRIVILEGES ON DATABASE parakh TO parakh_user;
   ```
2. In `.env`:
   ```
   DATABASE_URL=postgresql+psycopg2://parakh_user:change_me@localhost:5432/parakh
   ```
3. Re-run `python -m app.seed` (or use Alembic migrations for a managed
   schema history in a real deployment — an `alembic.ini` and `migrations/`
   folder are scaffolded for this).

### Running the test suite

```bash
cd backend
python -m pytest tests/ -v
```

This covers auth, the compliance engine's safety properties (low confidence
never auto-fails; verification never overwrites automated results; evidence
is never fabricated), and full pipeline integration tests via demo mode.

## 2. Web Dashboard

The dashboard is static HTML/CSS/JS — no build step.

```bash
cd dashboard
python3 -m http.server 5500
```

Visit `http://localhost:5500`. If your backend runs somewhere other than
`http://localhost:8000`, edit the one line at the top of `index.html`:

```html
<script>
  window.PARAKH_API_BASE = "http://localhost:8000";
</script>
```

Log in with either seeded account. Rules and Users management are visible
only to `ADMIN` accounts.

## 3. Flutter Mobile App

The mobile app source is under `mobile/`. It targets Android and iOS.

```bash
cd mobile
flutter pub get
flutter run
```

By default `ApiService` points at:
- `http://10.0.2.2:8000` on the Android emulator (maps to host loopback)
- `http://localhost:8000` on iOS simulator / desktop test runs

For a physical device, change `_defaultBaseUrl()` in
`lib/services/api_service.dart` to your machine's LAN IP, e.g.
`http://192.168.1.50:8000`, and make sure the backend is bound to
`0.0.0.0` (already the default in the run command above).

> **Note on this prototype submission:** the mobile source was written and
> statically reviewed (brace/import checks) but not compiled or run on a
> device/emulator in the environment used to build this repository, since
> no Flutter SDK was available there. The backend and web dashboard *were*
> run and tested end-to-end. Please run `flutter analyze` and `flutter run`
> locally as your first step with the mobile app.

## 4. Demo Mode (no camera needed)

For a quick presentation without a physical package or camera:

```bash
curl -X POST http://localhost:8000/api/demo/mostly_compliant/run \
  -H "Authorization: Bearer <token from /api/auth/login>"
```

Or from the dashboard/mobile app, look for the demo case list at
`GET /api/demo/cases` (a "Run Demo Case" affordance can be wired into any
frontend against this endpoint). Demo mode is also configurable via the
`DEMO_MODE` flag in `.env`.

## Troubleshooting

- **`pytesseract.TesseractNotFoundError`**: Tesseract isn't on your PATH.
  Set `TESSERACT_CMD` in `.env` to the full binary path.
- **`bcrypt` version errors during login/seed**: this project pins
  `bcrypt==4.0.1` in `requirements.txt` for compatibility with `passlib`;
  make sure you installed from `requirements.txt` rather than a stale
  environment.
- **CORS errors in the browser console**: confirm `window.PARAKH_API_BASE`
  in `dashboard/index.html` matches where your backend is actually running.
- **Images don't load in the dashboard/mobile evidence viewer**: confirm
  the backend's `/uploads` static mount is reachable (it's mounted
  automatically from `UPLOAD_DIR` in `main.py`) and that you're not behind
  a proxy stripping that path.

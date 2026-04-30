# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**E99 Berbagi** — a donation tracking and financial management web app for the Keluarga Elektro UI '99 alumni group. Tracks monthly donations from ~91 members and records disbursements to beneficiary families.

Live URL: https://donasie99.fly.dev

## Running Locally

```bash
# Default (uses db.json in project root as seed)
python app.py

# With a custom data directory
DATA_DIR=./data python3 app.py
```

App runs on `http://localhost:8080`. No build step required.

## Architecture

Three files make up the entire application:

- **`index.html`** (~2,258 lines) — Single-page app with three views (`#view-login`, `#view-dashboard`, `#view-admin`). All UI logic is vanilla JS.
- **`app.py`** (~47 lines) — Flask backend with three routes: `GET /` (serve index.html), `GET /api/data` (return db.json), `POST /api/save` (persist to `/data/db.json`).
- **`db.json`** — Seed database bundled in the repo. On first Fly.io boot, copied to the persistent volume at `/data/db.json`.

### Data Flow

- On page load, `loadDB()` calls `GET /api/data`, falls back to localStorage, then the bundled `DEFAULT_DB`.
- All admin mutations call `saveDB()`, which writes to localStorage and fires a non-blocking `POST /api/save` to the server.
- The server writes to `/data/db.json` (Fly.io persistent volume).

### Database Schema (`db.json`)

```json
{
  "settings": { "goal", "currency", "adminUser", "adminPass" (SHA-256) },
  "donors": ["DIODA-0052", ...],           // dropdown list only
  "recipientNames": ["Keluarga X", ...],   // display names only
  "donations": [{ "id", "donor", "amount", "date" (YYYY-MM), "notes" }],
  "recipients": [{ "name", "amount", "date" (YYYY-MM), "notes" }],
  "members": [{ "npm", "name", "code" }]   // 91 members
}
```

Key distinctions: `donors` and `recipientNames` are dropdown lists only — removing entries does not delete actual transaction records in `donations`/`recipients`. All dates are `"YYYY-MM"` strings. Amounts are plain integers (IDR). The anonymous donor code is `DIODA-99`.

## Deployment

Hosted on Fly.io, auto-deployed via GitHub Actions on every push to `main` (`.github/workflows/fly-deploy.yml`). Requires `FLY_API_TOKEN` secret in the repo.

**Critical:** The app must run exactly 1 Fly.io machine — multiple machines cause `db.json` write conflicts.

```bash
fly status
fly logs
fly deploy                                        # manual deploy
fly ssh console -C "cat /data/db.json" > db.json  # download live DB
fly scale count 1                                 # enforce single instance
```

## Key Implementation Notes

- The frontend password check uses `sha()` (SHA-256) before comparing against `settings.adminPass`.
- `context.md` in the repo root contains detailed documentation about the data model, CSV import workflow, member directory, and known data quirks — read it before making data-related changes.
- The source spreadsheet (`E99_Berbari.xlsx`) is not served to the web and is used only for batch data imports.

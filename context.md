# Project Context — Donasi Keluarga Elektro UI '99

## Overview
A web-based donation tracking app for **Keluarga Elektro UI '99** — a 1999 alumni group from the Electrical Engineering faculty at Universitas Indonesia. The app tracks monthly donations from members (donatur), records disbursements to recipients (penerima), and shows a financial summary dashboard. The group uses this to manage a rotating social fund called **E99 Berbagi**.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Single `index.html` (vanilla JS, no framework) |
| Backend | Python Flask (`app.py`) |
| Database | `db.json` (flat JSON file on Fly.io persistent volume) |
| Hosting | Fly.io — `https://donasie99.fly.dev` |
| Charts | Chart.js (loaded from CDN) |

The app started as a pure static HTML file (no backend). It was later migrated to Flask on Fly.io to enable server-side persistence.

---

## File Structure

```
donasiE99/
├── index.html          ← Entire frontend (HTML + CSS + JS in one file)
├── app.py              ← Flask server: serves index.html + /api/data + /api/save
├── db.json             ← Seed data (used only on first Fly.io deploy)
├── requirements.txt    ← Flask==3.0.0
├── Dockerfile          ← python:3.12-slim, exposes port 8080
├── fly.toml            ← Fly.io config (app=donasie99, region=sin, volume mount)
├── .gitignore          ← ignores __pycache__, .env, /data/
├── parse_csv.py        ← One-off script to convert monthly CSV report to db.json
├── E99_Berbagi.xlsx    ← Source monthly report spreadsheet (not served)
└── context.md          ← This file
```

---

## Data Model (db.json)

```json
{
  "settings": {
    "goal": 5000000,
    "currency": "IDR",
    "adminUser": "admin",
    "adminPass": "<SHA-256 hash of password>"
  },
  "donors": ["DIODA-99", "DIODA-0052", "..."],
  "recipientNames": ["Keluarga George", "Keluarga Tuwo", "..."],
  "recipients": [
    { "name": "Keluarga George", "amount": 750000, "date": "2024-11", "notes": "THR" }
  ],
  "donations": [
    { "id": "d0001", "donor": "DIODA-0052", "amount": 200000, "date": "2025-01", "notes": "" }
  ],
  "members": [
    { "npm": "049903001X", "name": "A. Ademulia Djufri", "code": "DIODA-001X" }
  ]
}
```

### Key distinctions
- **donors** — list of donor code strings for the Add Donation dropdown
- **recipientNames** — display-only list for the Record Disbursement dropdown; does NOT hold financial data
- **recipients** — actual disbursement records (financial data, one entry per event)
- **donations** — individual donation records from members
- **members** — 91 member directory entries linking full name, NPM, and donor code

### Date format
All dates stored as `"YYYY-MM"` (no day). e.g. `"2025-01"` for January 2025.

### Currency
Default is IDR. Amounts are plain integers (no decimals for IDR).

### Admin password
Stored as SHA-256 hash. Default password is `admin123`.
Hash: `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`

---

## Backend API (app.py)

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves index.html |
| `/api/data` | GET | Returns full db.json as JSON |
| `/api/save` | POST | Receives full db object, writes to /data/db.json |

### Data path logic
- On Fly.io: DATA_DIR=/data (persistent volume)
- Local dev: override with `DATA_DIR=./data python3 app.py`
- On first start, if /data/db.json does not exist, it is seeded from ./db.json

---

## Frontend Data Flow (index.html)

### loadDB()
1. Tries GET /api/data first (server is source of truth)
2. On success: caches to localStorage
3. On failure (no server): reads from localStorage
4. If localStorage also empty: falls back to DEFAULT_DB (empty arrays)

### saveDB()
1. Writes to localStorage synchronously
2. Non-blocking POST /api/save (silently ignored if server unavailable)

Every admin action calls saveDB(), so all changes persist to Fly.io automatically.

---

## Dashboard Features

- Hero section: monthly progress bar (donations vs target goal)
- 4 stat cards: Terkumpul Bulan Ini, Target Bulanan, Sisa Bulan Ini, Sisa Kas Donasi
- Sisa Kas Donasi = total all-time donations minus total all-time disbursements
- Month/Year filter pills: filters both recipients card and donations table
- Penerima Donasi card: disbursements list, 5 items default, expandable
- Ringkasan Keuangan chart: Chart.js mixed chart (bars + line for cumulative balance)
- All Donations table: searchable, sortable, 5 items default, expandable

---

## Admin Panel Layout (top to bottom)

### 1. Add New Donation | Donation History
- Donor dropdown (from db.donors), amount, month/year selects, notes
- History list newest-first with delete button per entry

### 2. Record Disbursement | Disbursement History
- Recipient dropdown (from db.recipientNames), amount, month/year, notes
- Multiple disbursements to the same recipient in the same month are allowed
- History list newest-first with delete button per entry

### 3. Member Lookup
- Real-time search across db.members by name, donor code, or NPM
- Shows avatar, full name, NPM, and donor code badge

### 4. Settings
- Target Donasi Bulanan: monthly goal + currency selector
- Change Password: SHA-256 hashed, current password verified before change
- Manage Donors: add/remove from donor dropdown (does NOT delete donation records)
- Manage Recipients: add/remove from recipient dropdown (does NOT delete disbursement records)
- Database section:
  - Export CSV: monthly breakdown with individual rows, subtotals, grand total
  - Export JSON: full db.json download (date-stamped)
  - Import JSON: replace entire database (with confirmation prompt)
  - Reset to committed: clears localStorage and re-fetches from server

---

## CSV Source Data Workflow

Monthly data comes from E99_Berbagi.xlsx. Steps:

1. Export sheet as e99donasi_new.csv (2-column: name | amount)
2. CSV structure per month block:
   - Month header row (e.g. "Laporan E99 Berbagi November 2024") marks start of block
   - Rows before "Pemasukan" = donors
   - "Pemasukan" = total income (skip)
   - Rows after "Pemasukan" before "Pengeluaran" = disbursement recipients
   - "Pengeluaran" = total spending (skip)
   - Rows after "Pengeluaran" = summary rows (skip: Saldo Sebelumnya, Kas Donasi, Sisa...)
3. Run parse_csv.py to generate db.json
4. Import via admin panel

---

## Member Directory

91 members from E99_NPM.csv. Columns: NPM, Nama, Kode Donatur.
Stored in db.members. Donor codes pattern: DIODA-XXXX.
Special entry: DIODA-99 = anonymous donor (Hamba ALLAH).

---

## Deployment

### A. Fly.io (legacy)

- App name: donasie99
- URL: https://donasie99.fly.dev
- Region: sin (Singapore)
- Machine: 1 shared CPU, 1GB RAM
- Volume: 1GB persistent named "data" mounted at /data
- IMPORTANT: always keep at exactly 1 machine (fly scale count 1)
  Running 2+ machines causes each to have its own separate db.json

#### Useful commands
```bash
fly status
fly logs
fly deploy
fly volumes list
fly ssh console
fly ssh console -C "cat /data/db.json" > db.json   # download live database
```

#### Database backup
```bash
fly ssh console -C "cat /data/db.json" > db.json
git add db.json
git commit -m "Backup db.json $(date +%Y-%m-%d)"
git push
```

---

### B. Home Server (primary)

- **Server:** Ubuntu home server at `/home/nandha/server/`
- **Domain:** `nandharu.uk` (Cloudflare)
- **Live URL:** https://donasie99.nandharu.uk
- **Architecture:** Cloudflare Tunnel → Nginx → Docker (zero exposed ports)

#### Traffic flow

```
Visitor → https://donasie99.nandharu.uk
    │
    ▼
┌──────────────────────────────┐
│  Cloudflare Edge             │  HTTPS termination, DDoS, WAF, caching
└──────────┬───────────────────┘
           │  encrypted tunnel (outbound-only from server)
           ▼
┌──────────────────────────────┐
│  cloudflare-tunnel           │  cloudflare/cloudflared:latest
│  network: server-net         │  no host ports
└──────────┬───────────────────┘
           │  http://nginx-gateway:80
           ▼
┌──────────────────────────────┐
│  nginx-gateway               │  nginx:alpine, rate limiting, security headers
│  network: server-net         │
└──────────┬───────────────────┘
           │  http://donasie99:8080
           ▼
┌──────────────────────────────┐
│  donasie99                   │  python:3.12-slim, gunicorn 1 worker, non-root
│  network: server-net         │  read-only fs, 512 MB RAM, 0.5 CPU
│  volume: donasi-data:/data   │
└──────────────────────────────┘
```

#### Key files added for home server deployment

| File | Purpose |
|---|---|
| `docker-compose.yml` | App container (joins server-net, named volume, hardened) |
| `Dockerfile` | Updated — non-root appuser, gunicorn, curl healthcheck, `/data` pre-created with correct ownership |
| `server-setup/nginx/donasie99.conf` | Nginx reverse proxy config |

#### Deployment steps (server already set up with aidatajakarta)

```bash
# 1. Clone repo
sudo git clone https://github.com/chikiball/donasiE99.git /home/nandha/server/sites/donasie99

# 2. Copy nginx config
sudo cp /home/nandha/server/sites/donasie99/server-setup/nginx/donasie99.conf \
        /home/nandha/server/nginx/conf.d/donasie99.conf

# 3. Build and start
cd /home/nandha/server/sites/donasie99
sudo docker compose up -d --build

# 4. Reload nginx
sudo docker exec nginx-gateway nginx -s reload
```

Then add a public hostname in Cloudflare (one.dash.cloudflare.com → Networks → Connectors → home-server → Public Hostname):

| Field | Value |
|---|---|
| Subdomain | `donasie99` |
| Domain | `nandharu.uk` |
| Type | `HTTP` |
| URL | `nginx-gateway:80` |

#### Useful commands

| Task | Command |
|---|---|
| View logs | `cd /home/nandha/server/sites/donasie99 && sudo docker compose logs -f --tail 50` |
| Redeploy | `sudo bash /home/nandha/server/scripts/deploy-site.sh donasie99` |
| Restart app | `cd /home/nandha/server/sites/donasie99 && sudo docker compose restart` |
| Reload nginx | `sudo docker exec nginx-gateway nginx -s reload` |
| Status dashboard | `sudo bash /home/nandha/server/scripts/status.sh` |
| Force rebuild | `cd /home/nandha/server/sites/donasie99 && sudo docker compose up -d --build --force-recreate` |

#### Database backup (home server)

```bash
sudo docker exec donasie99 cat /data/db.json > db.json
git add db.json
git commit -m "Backup db.json $(date +%Y-%m-%d)"
git push
```

#### IMPORTANT: gunicorn must run with 1 worker only
Multiple workers write `db.json` concurrently and will corrupt data. The `docker-compose.yml` enforces this via `CMD ["gunicorn", "--workers", "1", ...]`.

#### IMPORTANT: /data volume must be pre-created as appuser in the Dockerfile
Docker named volumes are initialized from the image at first mount. If `/data` isn't created and owned by `appuser` in the Dockerfile before `USER appuser`, the volume is owned by root and all writes to `db.json` silently fail — `saveDB()` in the frontend uses `.catch(function() {})` so the UI shows success even when the server write fails. The fix: `RUN useradd ... && mkdir -p /data && chown appuser:appuser /data`.

---

## Important Implementation Notes

### Making HTML/JS changes safely
The index.html file is large (~70KB). The file_edit tool has been unreliable for multi-line replacements. Preferred approach: bash + Python string replacement.

```python
from pathlib import Path
path = Path('index.html')
html = path.read_text(encoding='utf-8')
html = html.replace(old_string, new_string, 1)
path.write_text(html, encoding='utf-8')
```

Always verify after patching: check for HTML entities (&gt;, &quot;) in the script block which indicate corruption.

### View structure
Three sibling div.view elements:
- #view-login — login screen
- #view-dashboard — public dashboard (default)
- #view-admin — admin panel (requires login)

Only one active at a time via .active class. Never nest these inside each other.

### CSS variables
Colors defined in :root. Key: --primary (#4f46e5), --success (#059669), --danger (#dc2626), --text, --border, --card.

---

## Known Data Quirks

- Amounts like 666,667 or 333,333 are 1/3 splits of round amounts
- DIODA-99 is the anonymous donor code used across all months
- Recipients "Keluarga George", "Keluarga Tuwo", "Keluarga Rachmat" are regular monthly disbursement recipients
- Notes field on disbursements distinguishes multiple entries to the same recipient in the same month

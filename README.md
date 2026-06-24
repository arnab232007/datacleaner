# DataCleaner 🧹

Industry-grade data cleaning web application. Upload a CSV/XLS/XLSX file, run a
full automated cleaning pipeline, download the result as CSV or XLSX, and get a
PDF + interactive HTML quality report.

---

## Tech stack

| Layer | Libraries |
|---|---|
| Frontend | HTML5, Bootstrap 5, Tailwind CSS, Chart.js, Particles.js, AOS |
| Backend | Python 3.11+, Flask 3, Gunicorn |
| Data | Pandas 2, NumPy, Scikit-learn, SciPy, OpenPyXL |
| Reports | ReportLab (PDF), Plotly (HTML) |
| Infra | Docker, Docker Compose, Nginx, GitHub Actions |

---

## Quick start (local, no Docker)

### 1. Clone and set up Python

```bash
git clone https://github.com/your-org/datacleaner.git
cd datacleaner

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 3. Run the development server

```bash
cd backend
python app.py
```

Open http://localhost:5000 in your browser.

---

## Quick start (Docker)

```bash
# Development (Flask dev server, no Nginx)
docker compose up --build

# Production (Gunicorn + Nginx)
docker compose --profile prod up --build
```

The app is available at http://localhost (port 80) when using the prod profile,
or http://localhost:5000 for the dev profile.

---

## Project structure

```
datacleaner/
├── backend/
│   ├── app.py                  ← Flask app factory
│   ├── config/
│   │   └── settings.py         ← All configuration (env-overridable)
│   ├── routes/
│   │   ├── upload.py           ← POST /api/upload, GET /api/preview/<id>
│   │   ├── clean.py            ← POST /api/clean, GET /api/status|result
│   │   └── download.py         ← GET /api/download, /api/report
│   ├── services/
│   │   ├── cleaner.py          ← Pipeline orchestrator
│   │   ├── missing.py          ← Missing value imputation
│   │   ├── dedup.py            ← Duplicate removal
│   │   ├── types.py            ← Type correction
│   │   ├── outliers.py         ← IQR + Z-score outlier handling
│   │   ├── text.py             ← Text standardisation
│   │   ├── dates.py            ← Date parsing and ISO formatting
│   │   ├── colnames.py         ← Column name snake_case cleaning
│   │   └── report.py           ← PDF (ReportLab) + HTML (Plotly) reports
│   ├── utils/
│   │   ├── helpers.py          ← File helpers, cleanup thread, JSON responses
│   │   ├── validators.py       ← Upload and config validation
│   │   └── logger.py           ← Rotating file logger
│   ├── tests/
│   │   └── test_services.py    ← 15 pytest unit tests (all passing)
│   ├── uploads/                ← Temp raw files (auto-deleted after 1h)
│   ├── cleaned_files/          ← Output CSV / XLSX
│   ├── reports/                ← PDF / HTML quality reports
│   └── logs/                   ← app.log (rotating, 5 MB × 3)
├── frontend/
│   ├── index.html              ← Single-page app
│   └── static/
│       ├── css/styles.css      ← Dark glassmorphism theme
│       └── js/app.js           ← Upload, polling, charts, downloads
├── requirements.txt
├── Dockerfile                  ← Multi-stage build
├── docker-compose.yml
├── nginx.conf                  ← Reverse proxy config
└── .env.example
```

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload file → returns `file_id` + metadata |
| GET  | `/api/preview/<file_id>` | First 20 rows as JSON |
| POST | `/api/clean/<file_id>` | Start pipeline → returns `job_id` |
| GET  | `/api/status/<job_id>` | Poll progress: step, %, stats |
| GET  | `/api/result/<job_id>` | Full cleaning summary |
| GET  | `/api/download/<job_id>/<fmt>` | Stream cleaned file (csv \| xlsx) |
| GET  | `/api/report/<job_id>/<fmt>` | Quality report (pdf \| html) |

### Clean config (POST body)

```json
{
  "missing_num_strategy":   "median",
  "missing_cat_strategy":   "mode",
  "missing_drop_threshold": 0.6,
  "outlier_method":         "iqr",
  "outlier_action":         "cap",
  "zscore_threshold":       3.0,
  "clean_text":             true,
  "standardize_dates":      true,
  "clean_col_names":        true
}
```

---

## Running tests

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=term-missing
```

All 15 tests cover: missing values, deduplication, type correction, outlier
detection (IQR + Z-score), text standardisation, column name cleaning, and date
parsing.

---

## Deployment: Render.com (free tier)

1. Push to GitHub.
2. Create a new **Web Service** on Render, point it to your repo.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `cd backend && gunicorn --bind 0.0.0.0:$PORT "app:create_app()"`
5. Add environment variable `SECRET_KEY` in the Render dashboard.

## Deployment: Fly.io

```bash
fly launch --name datacleaner --region sin
fly secrets set SECRET_KEY=your-secret
fly deploy
```

## Deployment: VPS (Ubuntu)

```bash
# On server
git clone ... && cd datacleaner
docker compose --profile prod up -d --build

# Point your domain's A record to the server IP
# Add certbot for HTTPS:
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

---

## Configuration reference

All settings live in `backend/config/settings.py` and can be overridden via `.env`:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-change-me` | Flask secret key |
| `MISSING_NUM_STRATEGY` | `median` | Default numeric imputation |
| `OUTLIER_METHOD` | `iqr` | Default outlier detection |
| `OUTLIER_ACTION` | `cap` | Default outlier action |
| `FILE_TTL_SECONDS` | `3600` | Temp file lifetime |
| `MAX_CONTENT_LENGTH` | `52428800` | 50 MB max upload |

---

## License

MIT

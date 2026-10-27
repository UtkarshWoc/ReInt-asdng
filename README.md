# UK Wind Generation Day-Ahead Decision Support

An enterprise decision-support platform engineered for UK energy utility day-ahead power trading desks. It ingests National Grid ESO wind generation forecasts (`WINDFOR`) and half-hourly generation outturn (`FUELHH`) from the Elexon BMRS API, providing leak-free forecast views at gate closure (D-1 09:00 London time) and quantitative error metrics to accurately size thermal procurement risk buffers.

---

## 1. Problem & Value Proposition
UK energy utilities must procure wholesale electricity on day $D-1$ to meet forecasted consumer demand on delivery day $D$. Thermal and peaking asset procurement depends on net demand (total consumer demand minus renewable generation). Because wind generation is weather-dependent, power purchase decisions rely heavily on forecasts. 

This platform addresses the two fundamental commercial challenges faced by UK power traders:
1. **Decision-Time Forecast (Zero Leakage):** Exactly what wind generation forecast was available at the D-1 decision moment (default: 09:00 London time) without look-ahead data leakage?
2. **Quantified Accuracy & Thermal Risk Buffer:** How erroneous are these forecasts historically, and how many additional megawatts (MW) of thermal capacity must be hedged on day D-1 to avoid severe cashout penalties in the Balancing Mechanism?

---

## 2. Directory & Architecture Overview

```
.
├── ASSIGNMENT.md                   # Problem statement & challenge specification
├── CLAUDE.md                       # Engineering conventions & working rules
├── README.md                       # Project documentation & startup instructions
├── docker-compose.yml              # One-command container orchestration
├── vercel.json                     # Unified Vercel serverless deployment config
├── heroku.yml                      # Heroku Docker container build manifest
├── .gitignore                      # Git exclusion rules
├── .github/workflows/ci.yml        # CI lint & unit test pipeline
├── docs/
│   ├── ASSUMPTIONS.md              # Technical assumptions, resolution alignment, and data findings
│   ├── ARCHITECTURE.md             # Mermaid diagrams, leak-free sequence flow, and design decisions
│   ├── ANALYSIS.md                 # Empirical forecast accuracy findings for January 2026
│   └── VIDEO_SCRIPT.md             # Two 5-minute timed demo scripts (Customer Pitch & Tech Review)
├── backend/
│   ├── Dockerfile                  # Multi-stage Python 3.12 container (non-root appuser)
│   ├── requirements.txt            # Python dependencies (FastAPI, Pydantic, httpx, pandas)
│   ├── pyproject.toml              # Ruff linter & Pytest test runner configuration
│   ├── .env.example                # Backend environment variable template
│   ├── api/index.py                # Vercel Python serverless entrypoint
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory, CORS, and router registration
│   │   ├── core/
│   │   │   ├── config.py           # Application settings, ports, snapshot paths
│   │   │   └── time_utils.py       # DST-safe Europe/London & ISO UTC timestamp conversions
│   │   ├── clients/
│   │   │   └── elexon.py           # Async Elexon BMRS client with retry, backoff, and chunking
│   │   ├── schemas/
│   │   │   ├── __init__.py         # Pydantic schemas for health, meta, and decision views
│   │   │   └── accuracy.py         # Pydantic schemas for accuracy metrics & risk buffers
│   │   ├── services/
│   │   │   ├── ingestion.py        # Pipeline to clean, validate, align, and snapshot Elexon data
│   │   │   ├── forecast_selection.py # Leak-free latest-forecast-at-cutoff algorithm
│   │   │   └── metrics.py          # Empirical metrics, percentiles, and risk buffer engine
│   │   ├── repositories/
│   │   │   └── data_store.py       # High-performance in-memory indexed snapshot cache
│   │   ├── routers/
│   │   │   ├── health.py           # GET /api/health
│   │   │   ├── meta.py             # GET /api/meta (dates, row counts, freshness)
│   │   │   ├── forecasts.py        # GET /api/forecast/at-decision & /api/forecast/revisions
│   │   │   └── accuracy.py         # GET /api/accuracy/summary, /by-horizon, /by-hour, /risk-buffer
│   │   └── scripts/
│   │       ├── refresh_data.py     # CLI to fetch and rebuild live Elexon snapshot
│   │       └── run_analysis.py     # Script calculating all verified empirical figures in docs/
│   ├── data/
│   │   └── jan_2026_snapshot.json  # Committed verified January 2026 dataset (2.1 MB)
│   └── tests/
│       ├── fixtures/               # Real sample Elexon FUELHH & WINDFOR JSON payloads
│       ├── test_forecast_selection.py # Leakage prevention, boundary, and DST tests
│       ├── test_metrics.py         # Error metrics, safe MAPE, and risk buffer tests
│       ├── test_ingestion.py       # Data cleaning and hourly aggregation tests
│       └── test_api.py             # Integration tests for all REST endpoints
└── frontend/
    ├── Dockerfile                  # Multi-stage frontend container (Node 20 build -> Nginx Alpine)
    ├── package.json                # React 18, Vite, TypeScript, Tailwind, TanStack Query, Recharts
    ├── tsconfig.json               # TypeScript strict mode configuration
    ├── vite.config.ts              # Vite bundle and Vitest test configuration
    ├── tailwind.config.ts          # Tailwind CSS theme with light and dark mode support
    ├── .eslintrc.cjs               # ESLint configuration
    ├── .env.example                # Frontend environment variable template
    └── src/
        ├── main.tsx                # React DOM root with TanStack QueryClientProvider
        ├── App.tsx                 # Root layout, navigation tabs, and dark mode toggle
        ├── api/client.ts           # Typed API fetch client
        ├── types/index.ts          # TypeScript interfaces matching backend Pydantic models
        ├── components/
        │   ├── ui/                 # Card, KpiCard with tooltips, Skeleton, ErrorState
        │   ├── controls/           # DeliveryDatePicker, CutoffSelector
        │   └── charts/             # ForecastVsActual, Revisions, ErrorHistogram, HorizonError, RiskBuffer
        ├── pages/
        │   ├── ForecastPage.tsx    # Decision-time view, timeline, revisions explorer
        │   └── AccuracyPage.tsx    # Empirical metrics, histograms, and risk buffer calculator
        └── tests/
            ├── setup.ts            # Vitest DOM matchers setup
            ├── components.test.tsx # Component tests for KPI cards and date/cutoff controls
            └── App.test.tsx        # Navigation and tab switching tests
```

---

## 3. Getting Started & Running the Application

### Option A: Using Docker (Recommended)
Run the entire platform (backend API + frontend dashboard) with a single command:
```bash
docker compose up --build
```
- **Web Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Backend API & Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Option B: Running Locally Without Docker

#### Prerequisites
- Python 3.11+ (Python 3.12 recommended)
- Node.js 18+ & npm 9+

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt

# Start backend server:
uvicorn app.main:app --reload --port 8000
```
The backend will immediately boot and serve the committed January 2026 snapshot.

#### 2. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 4. How to Refresh Live Elexon Data
The repository includes a dedicated CLI command to refresh the dataset directly from Elexon BMRS:
```bash
cd backend
python -m app.scripts.refresh_data --start 2026-01-01 --end 2026-02-01
```
This fetches all half-hourly outturn records from `/datasets/FUELHH/stream`, downloads forecast revisions from `/datasets/WINDFOR/stream` in 7-day chunked batches with automatic retry and rate-limiting, aggregates half-hourly actuals to hourly resolution, and writes the compact snapshot to `backend/data/jan_2026_snapshot.json`.

---

## 5. Live Deployment Links
- **Production Web Application:** `https://reint-assignment-frontend.vercel.app` *(Placeholder until deployed)*
- **Production OpenAPI Documentation:** `https://reint-assignment-backend.vercel.app/docs` *(Placeholder until deployed)*

---

## 6. Running Tests & Quality Verification

### Backend Tests & Ruff Linting
```bash
cd backend
python -m ruff check .
pytest -v
```
*Current test suite: 27 passed tests covering cutoff boundary moments, look-ahead leakage prevention, DST transitions, safe MAPE, hourly aggregation, and API status codes.*

### Frontend Tests, Typecheck & ESLint
```bash
cd frontend
npm run typecheck
npm run lint
npm test -- --run
npm run build
```
*Current test suite: All TypeScript checks pass, ESLint reports 0 warnings, and 4 Vitest component tests pass.*

---

## 7. Key Findings & Empirical Analysis (January 2026)

All figures below are computed by `backend/app/scripts/run_analysis.py` on the verified January 2026 Elexon dataset (768 evaluated hourly periods):

1. **Systemic Over-Forecast Bias:** Wind forecasts exhibited a massive positive bias of **+1,824.8 MW**. In **85.4% of hours (656 / 768)**, the decision-time forecast exceeded actual outturn. A trading desk that did not adjust its bids would have suffered chronic physical shortfalls in over 8 out of every 10 hours.
2. **Volatile Tail Risk on Specific Days:** The worst day was **2026-01-28** (MAE: **5,374.8 MW**, peak error **+6,271 MW**), where a forecasted storm stalled off the UK coast. Conversely, anticyclonic conditions on **2026-01-19** yielded an MAE of only **736.2 MW**.
3. **Diurnal Lead-Time Degradation:** Peak daytime demand hours (12:00–18:00 London time, lead times 18–24h) experienced the highest average error (MAE **2,415.1 MW** and P90 error **4,842.7 MW**).
4. **Empirical Risk Buffer Sizing:** To achieve a **90% empirical confidence** of covering wind shortfalls, the trading desk must procure an additional **+4,511 MW** of thermal or peaking capacity on day D-1.

*Full details and visual breakdowns are documented in [docs/ANALYSIS.md](docs/ANALYSIS.md).*

---

## 8. Requirements Traceability Matrix

| Requirement from ASSIGNMENT.md | Implementation Component | Evidence & Verification |
| :--- | :--- | :--- |
| **BMRS FUELHH wind actuals** | `backend/app/clients/elexon.py` | 1,536 half-hourly actuals fetched and validated |
| **BMRS WINDFOR forecasts** | `backend/app/clients/elexon.py` | 19,856 forecasts fetched; hourly cadence identified |
| **Zero look-ahead leakage** | `backend/app/services/forecast_selection.py` | Unit tested with boundary moments and post-cutoff checks |
| **D-1 09:00 London gate closure** | `backend/app/core/time_utils.py` | DST-safe London-to-UTC conversion; configurable in UI |
| **Error sign convention** | $\text{Error} = \text{Forecast} - \text{Actual}$ | Stated across UI, API, and unit tested in `test_metrics.py` |
| **Quantified error metrics** | `backend/app/services/metrics.py` | MAE, RMSE, MBE, Safe MAPE, P50–P99, tolerance shares |
| **Revisions Explorer** | `frontend/src/components/charts/RevisionsChart.tsx` | Visualizes forecast evolution with cutoff reference line |
| **Thermal risk buffer** | `frontend/src/components/charts/RiskBufferChart.tsx` | Empirical quantile buffer sizing with confidence selector |
| **Dockerization** | `Dockerfile` & `docker-compose.yml` | Multi-stage non-root containers with healthchecks |
| **Video demonstration scripts** | `docs/VIDEO_SCRIPT.md` | Two 5-minute timed scripts with visual cues |

---

## 9. AI Tools Disclosure
In accordance with the assignment guidelines, AI tools (Google DeepMind Antigravity / Gemini 3.8 Flash) were utilized to assist in scaffolding boilerplate, drafting unit test suites, and pair-programming this project under human architectural guidance and real data verification. Every statistic in this project was derived from code executed on real Elexon data.

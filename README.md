# UK Wind Generation Day-Ahead Decision Support

A high-performance decision-support platform designed for UK energy utility day-ahead power trading teams. It aligns UK National Grid ESO wind generation forecasts (`WINDFOR`) with outturn generation (`FUELHH`) from Elexon BMRS, providing leak-free forecast views at gate closure (D-1 09:00 London time) and quantified error metrics to size thermal procurement risk buffers.

---

## 1. Problem & Product Overview
UK energy utilities must procure wholesale electricity on day $D-1$ to meet consumer demand on delivery day $D$. Thermal and peaking asset procurement depends on net demand (total demand minus renewable wind generation). This application addresses the two critical questions for power traders:
1. **Decision-Time Forecast:** What was the latest wind generation forecast available before the D-1 decision cutoff (preventing look-ahead data leakage)?
2. **Quantified Accuracy & Risk Buffer:** How erroneous are these forecasts historically, and how many extra megawatts (MW) of thermal capacity must be hedged at a given risk confidence level (e.g., P90)?

---

## 2. Directory & Architecture Overview

```
.
├── ASSIGNMENT.md                   # Problem statement & challenge specification
├── CLAUDE.md                       # AI pair-programming working rules & conventions
├── README.md                       # Project documentation & startup instructions
├── docker-compose.yml              # One-command local container stack
├── .github/workflows/ci.yml        # CI lint & unit test pipeline
├── docs/
│   ├── ASSUMPTIONS.md              # Technical assumptions, resolution alignment, and data findings
│   ├── ARCHITECTURE.md             # Architecture diagrams, data flow, and design decisions
│   ├── ANALYSIS.md                 # Empirical forecast accuracy findings for Jan 2026
│   └── VIDEO_SCRIPT.md             # Two 5-minute timed demo scripts (Customer & Tech Lead)
├── backend/
│   ├── Dockerfile                  # Multi-stage lightweight Python container
│   ├── requirements.txt            # Python dependencies (FastAPI, Pydantic, etc.)
│   ├── .env.example                # Example backend configuration
│   ├── api/index.py                # Vercel serverless entrypoint
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory & CORS
│   │   ├── core/                   # Configuration, logging, DST-safe time utilities
│   │   ├── clients/elexon.py       # Elexon BMRS API client with retry & rate-limiting
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # Forecast selection, metrics computation, ingestion
│   │   ├── repositories/           # Snapshot data store & cache
│   │   ├── routers/                # REST endpoints (/meta, /forecast, /accuracy)
│   │   └── scripts/                # Data refresh CLI and analysis scripts
│   ├── data/                       # Committed January 2026 snapshot
│   └── tests/                      # Pytest suite & real API fixtures
└── frontend/
    ├── Dockerfile                  # Multi-stage frontend container (Vite + Nginx)
    ├── package.json                # React 18, Vite, TypeScript, Tailwind, TanStack Query
    ├── .env.example                # Frontend environment configuration
    └── src/
        ├── components/             # Recharts visualizations, KPI cards, controls
        ├── pages/                  # ForecastPage and AccuracyPage
        └── ...
```

---

## 3. Getting Started

### Using Docker (Recommended)
Run the entire platform with one command:
```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API & Swagger: `http://localhost:8000/docs`

### Running Locally Without Docker

#### Backend
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Live Deployment Links
- **Production Web Application:** `[LIVE_APP_URL_PLACEHOLDER]`
- **Interactive OpenAPI Documentation:** `[LIVE_API_DOCS_URL_PLACEHOLDER]`

---

## 5. AI Assistance Disclosure
In accordance with the assignment guidelines, AI tools (Claude / Gemini Advanced Agentic Coding) were used to assist in scaffolding, test generation, and pair-programming this project under human architectural guidance and real data verification.

---

## 6. Requirements Traceability

| Requirement | Implementation Component | Verification Evidence |
| :--- | :--- | :--- |
| **BMRS FUELHH wind actuals** | `backend/app/clients/elexon.py` | Verified against live Elexon API; 1,536 half-hourly actuals |
| **BMRS WINDFOR forecasts** | `backend/app/clients/elexon.py` | 19,856 forecasts fetched; hourly cadence identified |
| **No look-ahead leakage** | `backend/app/services/forecast_selection.py` | Unit tested with boundary conditions, exact cutoff, and DST |
| **Trading decision cutoff** | `09:00` Europe/London on D-1 | Configurable in backend and frontend UI |
| **Error definition** | $\text{Error} = \text{Forecast} - \text{Actual}$ | Documented across all endpoints and UI views |
| **Comprehensive metrics** | MAE, RMSE, Bias, MAPE, P50-P99, Risk Buffer | Unit tested in `backend/tests/test_metrics.py` |
| **Interactive Dashboard** | React 18, Vite, Recharts, Tailwind CSS | Forecast vs Actual, Revisions, Error Histogram, Risk Buffer |
| **Docker & Deployment** | Root `docker-compose.yml`, Dockerfiles | Verified clean build and execution |

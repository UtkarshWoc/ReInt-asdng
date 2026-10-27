# Technical & Domain Assumptions

This document records all domain assumptions, data findings, resolution alignments, and surprises discovered in the Elexon dataset.

## 1. Trading Context & Decision Cutoff
- **User Role:** Day-ahead power trading desk at a UK energy utility procuring power to meet forecasted consumer net demand.
- **Decision Window:** Purchases for delivery day $D$ (00:00 to 24:00 UK local time) are committed on day $D-1$ at gate closure.
- **Gate Closure Cutoff:** `09:00` Europe/London time.
  - In January (GMT), 09:00 London time equals `09:00:00 UTC`.
  - In British Summer Time (BST), 09:00 London time equals `08:00:00 UTC`.
  - All comparisons are evaluated strictly in UTC after converting the London cutoff.
- **Date Scope:** Purchase decisions made in January 2026:
  - Decision days: `2026-01-01` through `2026-01-31`.
  - Delivery days: `2026-01-02` through `2026-02-01`.
  - Relevant forecasts published: from `2025-12-30 00:00:00 UTC` onwards.

## 2. Elexon BMRS Datasets
Only two datasets are used per the specification:
1. **Actual Generation:** Elexon `FUELHH/stream` filtered by `fuelType == "WIND"`.
   - Fields: `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, `generation`.
   - Native Cadence: Half-hourly (30-minute intervals: `:00` and `:30`).
   - January 2026 coverage: Exactly 48 settlement periods for every day, 0 missing records, 0 negative values.
2. **Forecast Generation:** Elexon `WINDFOR/stream`.
   - Fields: `publishTime`, `startTime`, `generation`.
   - Native Cadence: Strictly hourly target periods (`startTime` has minutes `:00`).
   - Publication Cadence: Published in batches every ~2 to 3 hours (typically at `:30` past the hour), covering horizons up to 72 hours ahead.
   - January 2026 coverage: 19,856 forecast records, 0 nulls, 0 negative values.

## 3. Resolution Mismatch & Data Alignment
- **Surprise / Discrepancy:** WINDFOR forecasts are hourly (24 periods/day), while FUELHH actuals are half-hourly (48 periods/day).
- **Alignment Strategy:**
  - Standard UK market convention: For each hourly target period `startTime = YYYY-MM-DDTHH:00:00Z`, the actual delivered energy is calculated as the mean of the two half-hour settlement periods:
    $$\text{Actual}_{\text{hourly}}(H) = \frac{\text{Actual}(H:00) + \text{Actual}(H:30)}{2}$$
  - Both individual 30-min actuals and the hourly aggregated actuals are maintained in the data model.
  - Exact match option: `startTime == startTime` (`:00` to `:00`) is also exposed for traders who want instantaneous top-of-hour comparisons.

## 4. Look-Ahead Leakage Prevention Logic
- For target period $T$ on delivery day $D$, and decision cutoff $C = \text{Date}(D-1) + \text{09:00 London}$:
  $$\text{Forecast}(T) = \arg\max_{P \le C} \text{Forecast}(T, P)$$
  where $P$ is the publication timestamp (`publishTime`).
- If no forecast was published with $P \le C$, the forecast is explicitly recorded as `None` (missing). A forecast published at $P > C$ is NEVER used.
- Exact boundary condition: If a forecast is published exactly at $P == C$, it was available at the cutoff moment and is valid for selection.

## 5. Error Definition & Key Metrics
- **Sign Convention:**
  $$\text{Error} = \text{Forecast} - \text{Actual}$$
  - $\text{Error} > 0$ (Positive): Over-forecast (expected wind generation exceeded actuals; shortfall must be procured from thermal/peaker assets).
  - $\text{Error} < 0$ (Negative): Under-forecast (actual generation exceeded expectations; energy surplus).
- **Metrics Reported:**
  - Mean Absolute Error (MAE): $\frac{1}{N} \sum |\text{error}|$
  - Root Mean Square Error (RMSE): $\sqrt{\frac{1}{N} \sum \text{error}^2}$
  - Mean Bias Error (MBE): $\frac{1}{N} \sum \text{error}$
  - Mean Absolute Percentage Error (MAPE): Calculated with a near-zero safeguard ($\text{actual} \ge 100\text{ MW}$) to prevent asymptotic distortion.
  - Empirical Error Quantiles: P50, P90, P95, P99 of $|\text{error}|$ and over-forecast error.
  - Risk Buffer: Empirical 90th percentile over-forecast error to determine the additional thermal capacity to procure to achieve a 90% confidence of supply.

## 6. Architecture & Deployment Decision (Vercel vs. Heroku)
- **Vercel as Primary Target:**
  - Frontend: React 18 + Vite static build deployed instantly on Vercel CDN.
  - Backend: FastAPI deployed on Vercel Python Serverless runtime (`api/index.py`).
  - Size Control: To guarantee staying well within Vercel's 50MB zipped / 250MB uncompressed limit, the backend serverless function relies on pure standard library and lightweight Pydantic v2 / FastAPI routines operating over a precomputed snapshot (`backend/data/jan_2026_snapshot.json`).
  - Heavy data manipulation (pandas, pyarrow) is isolated to the ingestion CLI (`python -m app.scripts.refresh_data`).
- **Container / Heroku Fallback:**
  - Full Docker container (`Dockerfile` + `docker-compose.yml`) provided and verified for 1-command local or Heroku container execution.

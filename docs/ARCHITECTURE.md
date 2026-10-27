# System Architecture & Technical Design

This document details the architectural design, data pipelines, leak-prevention mechanisms, API contracts, and deployment topology for the UK Wind Generation Day-Ahead Decision Support platform.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph External["External Data Sources (Elexon BMRS)"]
        F_API["FUELHH Endpoint\n(Half-hourly wind outturn)"]
        W_API["WINDFOR Endpoint\n(Hourly wind forecasts)"]
    end

    subgraph Pipeline["Data Ingestion Pipeline (Offline CLI)"]
        CLI["app.scripts.refresh_data"]
        CLEAN["Validation & Timestamp Normalization\n(UTC ISO-8601)"]
        ALIGN["Hourly Aggregation Engine\nMean(H:00, H:30)"]
        SNAP[("jan_2026_snapshot.json\n(Committed static snapshot)")]
        
        F_API --> CLI
        W_API --> CLI
        CLI --> CLEAN --> ALIGN --> SNAP
    end

    subgraph Backend["FastAPI Backend (Vercel Serverless / Docker)"]
        STORE["DataStore Repository\n(In-memory indexed cache)"]
        SELECTOR["Forecast Selection Engine\n(Enforces publishTime <= cutoff)"]
        METRICS["Accuracy & Risk Buffer Engine\n(MAE, RMSE, Bias, Quantiles)"]
        ROUTERS["REST API Routers\n(/meta, /forecast, /accuracy)"]

        SNAP --> STORE
        STORE --> SELECTOR
        STORE --> METRICS
        SELECTOR --> ROUTERS
        METRICS --> ROUTERS
    end

    subgraph Frontend["React 18 + Vite Frontend (Vercel CDN / Static)"]
        QUERY["TanStack Query Cache"]
        TAB_DEC["Forecast at Decision Tab\n(Delivery Date & Cutoff Pickers)"]
        TAB_ACC["Accuracy & Risk Sizing Tab\n(Empirical Buffer Calculator)"]
        RECHARTS["Recharts Visualization Engine"]

        ROUTERS --> QUERY
        QUERY --> TAB_DEC
        QUERY --> TAB_ACC
        TAB_DEC --> RECHARTS
        TAB_ACC --> RECHARTS
    end
```

---

## 2. Leak-Free Decision Logic Sequence

The core trading rule mandates that for any delivery day $D$, the trading desk commits purchases on day $D-1$ at the gate closure cutoff (default: `09:00 Europe/London`). Under no circumstances may a forecast published after this moment be utilized for day-ahead decisions.

```mermaid
sequenceDiagram
    autonumber
    actor Trader as Power Trading Desk
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant Store as DataStore Snapshot

    Trader->>UI: Select Delivery Date D and Cutoff (09:00 London)
    UI->>API: GET /api/forecast/at-decision?delivery_date=2026-01-05&cutoff=09:00
    API->>API: Parse delivery date and compute UTC cutoff (2026-01-04 09:00 UTC)
    loop For each hour T across Day D (00:00 to 23:00)
        API->>Store: Get candidate forecasts for target hour T
        API->>API: Filter candidates where publishTime <= Cutoff
        alt Eligible forecasts exist
            API->>API: Select latest forecast (argmax publishTime)
            API->>API: Compute horizon (T minus publishTime in hours)
        else No forecast published before cutoff
            API->>API: Mark forecast as missing (None)
        end
        API->>Store: Get hourly actual generation (mean of :00 and :30 outturns)
        API->>API: Compute error (Forecast minus Actual)
    end
    API->>API: Compute Day KPIs (Expected MWh, Peak MW, MAE, Missing Count)
    API-->>UI: Return 24 hourly periods and Day KPIs
    UI-->>Trader: Render interactive Forecast vs Actual chart and KPIs
```

---

## 3. Data Ingestion & Resolution Alignment

### Cadence Discrepancy & Solution
- **BMRS FUELHH:** Reported in 30-minute settlement periods (48 periods per day).
- **BMRS WINDFOR:** Issued in hourly resolution (`startTime` has minutes `:00`).
- **Alignment Strategy:**
  To evaluate energy delivery over the 1-hour contract block $H$, the actual generation is calculated as the arithmetic average of the two half-hour settlement periods:
  $$\text{Actual}_{\text{hourly}}(H) = \frac{\text{Actual}(H:00) + \text{Actual}(H:30)}{2}$$
  Both the individual 30-minute records (`period_00` and `period_30`) and the aggregated hourly average are preserved in the data store.

### Data Cleaning Rules
1. **Timestamp Normalization:** All timestamps converted to ISO-8601 UTC ending in `Z`.
2. **Value Validation:** Negative generation figures are rejected as telemetry corruptions.
3. **Deterministic Deduplication:** Ingestion enforces a unique key on `(publishTime, startTime)` to avoid duplicate entries during chunked queries.

---

## 4. Error Metrics & Empirical Risk Sizing Engine

### Sign Convention
$$\text{Error} = \text{Forecast} - \text{Actual}$$
- **Positive Error ($\text{Error} > 0$):** Over-forecast. Wind generation fell short of expectations; the trading desk faces physical shortfall penalties in the Balancing Mechanism.
- **Negative Error ($\text{Error} < 0$):** Under-forecast. Wind generation exceeded expectations; energy surplus.

### Mathematical Formulations
- **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N} \sum_{i=1}^N |\text{Forecast}_i - \text{Actual}_i|$
- **Root Mean Square Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (\text{Forecast}_i - \text{Actual}_i)^2}$
- **Mean Bias Error (MBE):** $\text{MBE} = \frac{1}{N} \sum_{i=1}^N (\text{Forecast}_i - \text{Actual}_i)$
- **Safe MAPE:** Evaluated exclusively on hours where $\text{Actual}_i \ge 100\text{ MW}$ to prevent division by near-zero:
  $$\text{MAPE}_{\text{safe}} = \frac{1}{K} \sum_{\text{Actual}_i \ge 100} \frac{|\text{Forecast}_i - \text{Actual}_i|}{\text{Actual}_i} \times 100\%$$
- **Empirical Risk Buffer:**
  Given target confidence quantile $q \in [0.50, 0.99]$ and empirical over-forecast errors $\mathcal{E}^+ = \{e_i \mid e_i > 0\}$:
  $$\text{Buffer}(q) = \text{Quantile}_q(\mathcal{E}^+)$$
  $$\text{Wind}_{\text{conservative}} = \max\left(0, \text{Forecast} - \text{Buffer}(q)\right)$$
  $$\text{Thermal Procurement} = \text{Demand} - \text{Wind}_{\text{conservative}}$$

---

## 5. Deployment Architecture

### Primary Deployment Target: Vercel (Unified Serverless & CDN)
- **Frontend:** Built via Vite as an optimized static bundle and served across Vercel's global edge CDN.
- **Backend:** FastAPI exposed via `backend/api/index.py` using `@vercel/python`.
- **Zero Heavy Dependencies at Serving Time:** The API server operates in pure standard library + Pydantic v2 over the committed JSON snapshot (`backend/data/jan_2026_snapshot.json`). This keeps the serverless package under 15 MB (far below Vercel's 50 MB compressed limit) with cold starts under 150 ms.

### Container Fallback: Docker & Heroku
- **Multi-Stage Builds:** `backend/Dockerfile` and `frontend/Dockerfile` leverage multi-stage compilation and non-root users (`appuser`).
- **One-Command Orchestration:** `docker-compose.yml` mounts both services with automated healthchecks:
  ```bash
  docker compose up --build
  ```
- **Heroku Manifest:** `heroku.yml` enables containerized deployment to Heroku Dynos without buildpack configuration.

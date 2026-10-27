# System Architecture & Design Decisions

This document details the architectural design, data pipelines, leak-prevention mechanisms, and deployment topology for the UK Wind Generation Decision Support platform.

## 1. System Context & Overview

```mermaid
flowchart TD
    subgraph External["External Data Sources (Elexon BMRS)"]
        F_API["FUELHH Endpoint\n(Half-hourly wind outturn)"]
        W_API["WINDFOR Endpoint\n(Hourly wind forecasts)"]
    end

    subgraph Ingestion["Ingestion & Pipeline (Offline / Refresh CLI)"]
        CLI["refresh_data.py"]
        CLEAN["Clean, validate, & align"]
        SNAP[("jan_2026_snapshot.json\n(Committed static snapshot)")]
        F_API --> CLI
        W_API --> CLI
        CLI --> CLEAN --> SNAP
    end

    subgraph Backend["FastAPI Backend (Vercel Serverless / Docker)"]
        STORE["DataStore Repository\n(In-memory cached snapshot)"]
        SELECTOR["Forecast Selection Engine\n(Leak-free cutoff logic)"]
        METRICS["Accuracy & Risk Engine\n(MAE, RMSE, Bias, P90 Buffer)"]
        ROUTERS["REST API Routers\n(/meta, /forecast, /accuracy)"]

        SNAP --> STORE
        STORE --> SELECTOR
        STORE --> METRICS
        SELECTOR --> ROUTERS
        METRICS --> ROUTERS
    end

    subgraph Frontend["React + Vite Frontend (Vercel CDN / Static)"]
        QUERY["TanStack Query Client"]
        P_DEC["Forecast at Decision Tab\n(D-1 Cutoff Picker, Timeline, Revisions)"]
        P_ACC["Accuracy & Risk Tab\n(KPIs, Histograms, Risk Buffer, Horizons)"]
        RECHARTS["Recharts Visualization Engine"]

        ROUTERS --> QUERY
        QUERY --> P_DEC
        QUERY --> P_ACC
        P_DEC --> RECHARTS
        P_ACC --> RECHARTS
    end
```

## 2. Leak-Free Decision Logic

```mermaid
sequenceDiagram
    autonumber
    actor Trader as Power Trader
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant Store as DataStore Snapshot

    Trader->>UI: Select Delivery Day D & Cutoff (e.g. 09:00 London)
    UI->>API: GET /api/forecast/at-decision?delivery_date=D&cutoff=09:00
    API->>API: Compute cutoff timestamp in UTC: C = (D-1)T09:00 London
    API->>Store: Query WINDFOR forecasts for target hours T on Day D
    API->>API: Filter: publishTime <= C
    API->>API: Select: argmax(publishTime) for each target hour T
    API->>Store: Query FUELHH actuals for target hours on Day D
    API->>API: Compute KPIs (Expected MWh, Peak MW, Min MW, Horizons)
    API-->>UI: Return 24 hourly periods with latest forecast, publishTime, and actual
    UI-->>Trader: Render Forecast vs Actual chart & Decision KPIs
```

## 3. Technology Stack & Directory Structure
- **Backend:** Python 3.12, FastAPI, Pydantic v2, pytest, ruff, mypy.
- **Frontend:** React 18, Vite, TypeScript, TanStack Query v5, Recharts, Tailwind CSS.
- **Data Store:** Compact snapshot loaded at startup into memory for sub-millisecond query responses.
- **Containerization:** Multi-stage Docker builds with non-root security.

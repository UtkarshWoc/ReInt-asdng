# Video Demo Scripts

This document provides two complete, timed presentation scripts for the demonstration video. Each part is designed to be spoken at an executive cadence of approximately **130 words per minute** (under 5 minutes each, maximum 10 minutes total).

---

# Part 1: Customer Pitch & Decision Support Walkthrough
**Target Duration:** 4 minutes 45 seconds (~620 words)  
**Audience:** Commercial Director & Day-Ahead Power Trading Desk at a UK Energy Utility  
**Tone:** Persuasive, outcome-driven, high-conviction; zero technical code jargon.

---

### [00:00 – 00:45] The Trading Desk's Dilemma: Day-Ahead Wind Volatility
- **On Screen:** Title slide showing *"UK Wind Day-Ahead Decision Support: Hedging Renewable Volatility"* transitioning to the live web application in light mode.
- **Spoken Script (100 words):**
  > "Good morning. In the UK day-ahead power market, trading teams face a multi-million-pound challenge every single day. To supply our retail and commercial customers, we must commit our power purchases on day D-minus-one at gate closure—09:00 London time. 
  > 
  > The volume of expensive thermal power we buy depends directly on net demand: total consumer demand minus forecasted wind generation. But wind is notoriously volatile. If the wind underperforms, we are caught short in the Balancing Mechanism, paying extreme cashout penalties. If wind overperforms, we spill surplus energy at distress prices. 
  > 
  > Today, I'm proud to present the pilot output of our Day-Ahead Decision Support platform."

---

### [00:45 – 02:00] The Decision-Time View: Pure Gate-Closure Reality
- **On Screen:** The **Forecast at Decision** tab. Cursor hovers over the Date Picker (selecting `2026-01-05`), points out the D-1 09:00 London Cutoff badge, then highlights the KPI cards and the Forecast vs Actual chart.
- **Spoken Script (165 words):**
  > "Let's step into the shoes of a day-ahead trader at 08:50 on January 4th, purchasing power for delivery on January 5th. 
  > 
  > What was the actual wind generation forecast available before the 09:00 cutoff? The platform filters out any later forecast to guarantee zero hindsight leakage. For January 5th, the desk saw an expected total generation of 296 gigawatt-hours, peaking at 14,142 megawatts around 17:00, with a baseload minimum of 10,700 megawatts.
  > 
  > Notice the interactive chart: the green curve represents our exact decision baseline. In hindsight, we overlay the actual outturn in dotted blue. On this specific day, actual wind generation closely tracked the forecast during morning hours, but started dropping below forecast in the evening peak. 
  > 
  > Looking at our lead-time table below, we see exactly which publication batch fed each hour—typically published at 07:30 UTC, providing a 16-to-40-hour lead time."

---

### [02:00 – 03:15] The Revisions Explorer & January Accuracy Reality
- **On Screen:** Click the **Forecast Revisions Explorer** dropdown, selecting hour 18:00. Show how the forecast shifted across time, with the amber vertical cutoff line. Then switch to the **Forecast Accuracy** tab.
- **Spoken Script (165 words):**
  > "If a trader wants to know how unstable a forecast was, our Revisions Explorer shows how forecasts evolved leading up to delivery. The amber vertical line marks our 09:00 gate closure. Only forecasts to the left were available for our bid.
  > 
  > Now, how accurate were these forecasts across the entire month of January? Let's switch to the Forecast Accuracy tab.
  > 
  > Over all 768 evaluated hours in January 2026, the Mean Absolute Error was 2,107 megawatts. But here is the critical discovery: the Mean Bias was positive 1,825 megawatts. In 85.4% of all hours, the official forecast overestimated wind generation! 
  > 
  > Unadjusted bidding would have left our utility physically short in more than eight out of every ten hours."

---

### [03:15 – 04:45] Sizing the Thermal Risk Buffer & Business Value
- **On Screen:** Scroll down to the **Empirical Risk Buffer & Thermal Procurement Sizing** section. Adjust the confidence slider from 75% to 90%, showing the chart update in real-time.
- **Spoken Script (190 words):**
  > "How do we protect our business against this chronic shortfall? This is where our Empirical Risk Buffer delivers tangible bottom-line value.
  > 
  > Rather than gambling on the unadjusted forecast, our model calculates the empirical 90th percentile of over-forecast error: 4,511 megawatts. 
  > 
  > We apply this buffer directly to the forecast, deriving a Conservative Wind Baseline—shown here by the amber line. The formula is simple and robust: Thermal Procurement equals Customer Demand minus Conservative Wind.
  > 
  > By purchasing an additional 4,511 megawatts of flexible thermal generation on day D-minus-one, our trading desk achieves 90% empirical certainty that our wind delivery shortfall will be completely hedged. As shown on the chart, the actual blue outturn stays safely above our conservative baseline across the entire delivery day.
  > 
  > In volatile winter months, this hedging strategy eliminates severe imbalance settlement penalties and protects utility operating margins. 
  > 
  > This platform turns weather uncertainty into quantified commercial confidence. Thank you."

---

# Part 2: Technical Lead Review & Architecture Tour
**Target Duration:** 4 minutes 50 seconds (~630 words)  
**Audience:** Internal Technical Lead & Senior Engineering Reviewers  
**Tone:** Precise, technical, architectural, rigorous; emphasizing testability, code quality, and trade-offs.

---

### [00:00 – 00:50] Architectural Overview & Ingestion Topology
- **On Screen:** Open `docs/ARCHITECTURE.md` showing the high-level Mermaid diagram, then terminal showing file tree.
- **Spoken Script (110 words):**
  > "Hi team. Today I'm presenting the technical implementation of the UK Wind Decision Support platform. 
  > 
  > The system is architected in three decoupled layers:
  > First, an offline ingestion pipeline in `backend/app/clients/elexon.py` and `services/ingestion.py` that queries Elexon BMRS `FUELHH` and `WINDFOR` stream APIs.
  > Second, a high-performance FastAPI service that operates over an in-memory indexed snapshot in `backend/app/repositories/data_store.py`.
  > And third, a responsive React 18 single-page application built with TypeScript, Vite, Tailwind CSS, TanStack Query, and Recharts.
  > 
  > Let's look at how we resolved key domain and data challenges."

---

### [00:50 – 01:50] Leak-Free Cutoff Logic & DST Resolution Alignment
- **On Screen:** Show code for `backend/app/services/forecast_selection.py` (`select_latest_forecast_at_cutoff`) and `backend/app/core/time_utils.py` (`get_decision_cutoff_utc`).
- **Spoken Script (135 words):**
  > "The primary business requirement is zero look-ahead data leakage. In `forecast_selection.py`, for every hourly target period on delivery day D, we strictly filter candidate forecasts with `publishTime <= cutoff_utc`, taking the greatest publish time. If no forecast exists prior to cutoff, we explicitly mark it as missing rather than leaking future data.
  > 
  > Boundary conditions are strictly unit-tested: a forecast published exactly at the cutoff second is valid, while a single second later is rejected.
  > 
  > Timezones are handled in `core/time_utils.py`. All internal storage and API payloads use ISO-8601 UTC. The cutoff is evaluated in `Europe/London`, ensuring that during GMT 09:00 London is 09:00 UTC, while during British Summer Time it correctly maps to 08:00 UTC.
  > 
  > For data alignment, FUELHH 30-minute outturns are aggregated into 1-hour blocks via the mean of settlement periods :00 and :30."

---

### [01:50 – 02:50] API Contracts & Empirical Metrics Engine
- **On Screen:** Open Swagger UI (`http://localhost:8000/docs`) showing `/api/meta`, `/api/forecast/at-decision`, and `/api/accuracy/*`, then show `backend/app/services/metrics.py`.
- **Spoken Script (130 words):**
  > "All REST endpoints are documented with OpenAPI and typed using Pydantic v2 schemas in `backend/app/schemas/`.
  > 
  > In `services/metrics.py`, we implement the strict error convention: `Error = Forecast - Actual`. 
  > Beyond standard MAE and RMSE, we calculate Mean Bias Error, empirical percentiles (P50 through P99), and a safe MAPE that filters out actual generation under 100 megawatts to prevent division-by-near-zero asymptotic distortion.
  > 
  > The `/api/accuracy/risk-buffer` endpoint isolates positive over-forecast errors and computes the empirical quantile for the user's selected confidence level. 
  > In `data_store.py`, dictionary lookups indexed by `startTime` allow all 24 periods and KPIs to be computed in less than 2 milliseconds."

---

### [02:50 – 03:50] Frontend Architecture & UX State Management
- **On Screen:** Show `frontend/src/App.tsx`, `ForecastPage.tsx`, and `components/charts/ForecastVsActualChart.tsx`.
- **Spoken Script (130 words):**
  > "On the frontend, we use React 18 with TypeScript in strict mode. Server state is managed using TanStack Query v5 with automatic background caching and stale-time controls.
  > 
  > Custom UI components in `components/ui/` provide loading skeletons, accessible cards, and an error boundary state. We built six custom Recharts components in `components/charts/`, featuring custom tooltips that display both UTC and London local time, exact megawatt values, and forecast lead horizons.
  > 
  > The user can dynamically toggle between Light and Dark mode, with Tailwind CSS managing clean color palettes. The user interface displays explicit metric explanations and sign convention reminders across all pages to prevent any trader misinterpretation."

---

### [03:50 – 04:50] Testing, CI, Dockerization & Deployment Strategy
- **On Screen:** Terminal showing `pytest` running with 27 passed tests, then GitHub Actions `ci.yml`, and `docker-compose.yml`.
- **Spoken Script (125 words):**
  > "For quality assurance, our backend test suite in `backend/tests/` contains 27 unit and integration tests covering cutoff boundaries, leakage prevention, DST transitions, and API error codes. The frontend test suite runs in Vitest with React Testing Library. Both Ruff linting and TypeScript checks pass with zero warnings.
  > 
  > Our GitHub Actions CI workflow in `.github/workflows/ci.yml` validates linting, typechecking, and tests on every push.
  > 
  > For deployment, we configured a dual topology:
  > First, a unified Vercel deployment where the frontend runs as a static edge build and the FastAPI backend runs as a lightweight serverless function under 15 megabytes.
  > Second, full containerization via multi-stage Dockerfiles and `docker-compose.yml`, which starts the entire stack locally with a single command.
  > 
  > The codebase is clean, reproducible, and ready for production."

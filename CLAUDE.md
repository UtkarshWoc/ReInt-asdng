# Working Rules & Conventions (CLAUDE.md)

## 1. Operating Identity & Anonymity
- **Git identity:**
  - `user.name = anon-dev`
  - `user.email = anon-dev@users.noreply.github.com`
- **Strict Anonymity:** Never include any real personal names, emails, company/employer names, or university references in any file, comment, commit, or pull request.

## 2. Domain & Business Rules
- **User Role:** Day-ahead power trading team at a UK energy utility.
- **Decision Window:** Power purchase decisions for delivery day $D$ are committed on day $D-1$ at the gate closure cutoff: `09:00` London time (`Europe/London`).
- **Core Needs:**
  1. Latest wind generation forecast available at decision cutoff time (no look-ahead leakage).
  2. Quantified forecast accuracy metrics (MAE, RMSE, bias, quantiles, horizon degradation) to hedge procurement error.
- **Look-Ahead Leakage Prevention:**
  - For target period `startTime` on delivery day $D$, the forecast used MUST be the latest forecast published with `publishTime <= cutoff_utc`.
  - If no forecast was published at or before cutoff, mark it as missing (`None`); NEVER leak a forecast published after cutoff.
- **Error Definition:**
  $$\text{error} = \text{forecast} - \text{actual}$$
  - Positive error ($\text{error} > 0$): Over-forecast (expected more wind than actually delivered; shortfall must be procured elsewhere).
  - Negative error ($\text{error} < 0$): Under-forecast (generated more wind than expected; surplus spill or curtailment).
- **Timezone Conventions:**
  - Internal storage & API responses: Strictly ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
  - Cutoff evaluation: `Europe/London` (converts cleanly between GMT in winter and BST in summer).
  - UI display: Explicitly labeled in UK Local Time (`Europe/London`) alongside UTC.

## 3. Data Integrity & Verification
- **Data Sources:** ONLY Elexon BMRS `FUELHH` (WIND actuals) and `WINDFOR` (forecasts).
- **No Fabricated Numbers:** All figures in documentation, analysis, scripts, or video scripts must be computed from real data via verifiable code in the repository.
- **Surface Surprises:** Explicitly record resolution differences (FUELHH 30-min vs WINDFOR 60-min), missing intervals, and anomalies in `docs/ASSUMPTIONS.md`.

## 4. Development & Commit Protocol
- **Conventional Commits:** e.g. `feat(backend): ...`, `test(core): ...`, `docs: ...`, `fix: ...`.
- **Pre-commit Checks:** Run tests and linter before every commit.
- **User Push Only:** The agent never executes `git push`. Output the exact `git push` command for the user.
- **Status Reporting:** At the end of every phase, state what works, what was tested, what was not tested, and any known issues.

## 5. Technology Stack & Deployment Architecture
- **Backend:** Python 3.12, FastAPI, Pydantic v2, httpx, pandas (ingestion pipeline), pytest, ruff.
- **Frontend:** React 18, Vite, TypeScript, TanStack Query, Recharts, Tailwind CSS, Lucide icons, Vitest.
- **Deployment Strategy:**
  - Primary: Vercel (static Vite frontend + serverless FastAPI backend serving precomputed snapshot).
  - Fallback / Containerized: Heroku / Docker container via multi-stage Dockerfiles and `docker-compose.yml`.

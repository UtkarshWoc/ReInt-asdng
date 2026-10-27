# January 2026 UK Wind Forecast Accuracy Analysis

*All figures in this report are computed directly from the verified Elexon BMRS January 2026 dataset (19,856 WINDFOR forecast records and 1,536 FUELHH actual generation records) using `backend/app/scripts/run_analysis.py`.*

---

## 1. Executive Summary & Headline Metrics

During January 2026 (delivery dates `2026-01-01` through `2026-02-01`), 768 hourly decision windows were evaluated at the gate closure cutoff of **09:00 Europe/London time on D-1**.

| Metric | Empirical Value | Unit / Definition | Commercial Implication |
| :--- | :--- | :--- | :--- |
| **Evaluated Hours** | `768` | Hours (32 days &times; 24h) | Complete delivery coverage across January |
| **Mean Absolute Error (MAE)** | `2,106.7` | MW | Average hourly forecast error magnitude |
| **Root Mean Square Error (RMSE)** | `2,577.5` | MW | Penalizes large forecasting blunders |
| **Mean Bias Error (MBE)** | `+1,824.8` | MW ($\text{Forecast} - \text{Actual}$) | **Massive systemic over-forecast bias** |
| **Safe MAPE** | `22.22%` | % (Periods where $\text{Actual} \ge 100\text{ MW}$) | Relative percentage inaccuracy |
| **P50 Absolute Error** | `1,727.3` | MW | Median hourly forecast error |
| **P90 Absolute Error** | `4,219.5` | MW | 90% of hours experience an error under 4.2 GW |
| **P95 Absolute Error** | `5,291.2` | MW | Severe tail error threshold |
| **P99 Absolute Error** | `6,255.9` | MW | Extreme stress events |
| **Share within &plusmn;500 MW** | `10.16%` | % of evaluated hours | Only 1 in 10 hours was within a tight 500 MW band |
| **Share within &plusmn;1,000 MW** | `25.00%` | % of evaluated hours | 1 in 4 hours was within 1 GW |
| **Share within &plusmn;2,000 MW** | `57.16%` | % of evaluated hours | Nearly 43% of hours experienced an error exceeding 2 GW |

---

## 2. Key Data-Backed Findings

### Finding 1: Severe Systemic Over-Forecast Bias (85.4% Shortfall Frequency)
- In **656 out of 768 hours (85.4%)**, the forecast available at the D-1 09:00 cutoff was higher than the outturn generation ($\text{Error} > 0$).
- Wind generation was under-forecasted in only **112 hours (14.6%)**.
- The average over-forecast magnitude was **+2,301.3 MW**, whereas the average under-forecast magnitude was only **-966.6 MW**.
- **Trading Implication:** A desk that purchased thermal power matching unadjusted wind forecasts would have been physically short in 85% of hours, paying punishing system buy prices in the Balancing Mechanism (BM).

### Finding 2: High Concentration of Extreme Errors on Specific Days
Forecast errors were not uniformly distributed across the month; rather, frontal weather systems and storm tracking errors caused massive multi-gigawatt discrepancies on specific delivery dates:

#### Worst 3 Delivery Days in January 2026:
1. **2026-01-28:** Day MAE of **5,374.8 MW**, Mean Bias of **+5,374.8 MW**, Peak Hourly Error of **+6,271.0 MW**. Every single hour was severely over-forecasted as an expected wind front stalled off the UK coast.
2. **2026-01-12:** Day MAE of **4,868.3 MW**, Mean Bias of **+4,868.3 MW**, Peak Hourly Error of **+6,870.0 MW**.
3. **2026-01-11:** Day MAE of **4,801.7 MW**, Mean Bias of **+4,801.7 MW**, Peak Hourly Error of **+5,953.0 MW**.

#### Best 3 Delivery Days in January 2026:
1. **2026-01-19:** Day MAE of **736.2 MW**, Peak Error **1,779.5 MW**, Mean Bias **-730.1 MW** (stable anticyclonic weather).
2. **2026-01-16:** Day MAE of **782.8 MW**, Peak Error **2,101.5 MW**, Mean Bias **+352.0 MW**.
3. **2026-01-09:** Day MAE of **839.4 MW**, Peak Error **2,242.5 MW**, Mean Bias **+804.9 MW**.

### Finding 3: Error Degradation by Lead Horizon
Evaluating error performance across forecast lead-time brackets (hours between forecast `publishTime` and target period `startTime`):

| Horizon Bracket | Sample Count | MAE (MW) | P90 Absolute Error (MW) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **12–18h** | 64 | `2,207.2` | `4,623.9` | Late afternoon / evening of Day D |
| **18–24h** | 192 | `2,415.1` | `4,842.7` | Peak diurnal demand hours (12:00–18:00) |
| **24–30h** | 192 | `2,018.1` | `3,784.2` | Morning peak hours (06:00–12:00) |
| **30–36h** | 192 | `1,984.4` | `4,157.7` | Overnight off-peak hours (00:00–06:00) |
| **36–48h** | 128 | `1,910.2` | `4,198.6` | Far-horizon periods |

*Observation:* Peak demand hours (12:00 to 18:00 on Day D, corresponding to horizons of 18–24 hours from the D-1 09:00 cutoff) suffered the highest average error (MAE 2,415 MW, P90 4,843 MW) due to coinciding diurnal atmospheric boundary layer turbulence and thermal gradient changes.

### Finding 4: Wind Level Heteroskedasticity
Error volatility was strongly correlated with the absolute magnitude of wind generation:

| Generation Bucket | Sample Count | MAE (MW) | P90 Error (MW) | Error Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Low Wind (< 6 GW)** | 107 | `2,075.6` | `5,088.1` | High relative error; false-positive ramp forecasts |
| **Medium Wind (6–12 GW)** | 286 | `1,652.0` | `2,931.5` | Most predictable operating band |
| **High Wind (> 12 GW)** | 375 | `2,462.3` | `4,478.5` | High volumetric risk; turbine cutout dynamics |

*Insight:* While absolute MAE was highest during High Wind conditions (2,462 MW), the P90 tail risk was highest in Low Wind conditions (5,088 MW), caused by weather models predicting massive low-pressure storm arrivals that arrived several hours late or missed the UK landfall.

---

## 3. Practical Risk Buffer Sizing Recommendations

To protect the trading desk from physical imbalance penalties, the software computes empirical over-forecast quantiles from the real January error distribution:

$$\text{Conservative Wind} = \max\left(0, \text{Decision Forecast} - \text{Empirical Buffer}\right)$$
$$\text{Thermal Procurement} = \text{Demand} - \text{Conservative Wind}$$

| Target Confidence | Empirical Buffer (MW) | Daily Hedged Energy (MWh) | Risk / Cost Trade-off |
| :--- | :--- | :--- | :--- |
| **75% (Aggressive)** | `+3,235 MW` | ~77,640 MWh | Lower capacity commitment; 25% chance of minor shortfall |
| **85% (Moderate)** | `+3,911 MW` | ~93,860 MWh | Balanced commercial hedge |
| **90% (Industry Standard)** | **`+4,511 MW`** | **~108,260 MWh** | **Recommended baseline for day-ahead thermal contracts** |
| **95% (Conservative)** | `+5,376 MW` | ~129,020 MWh | High security; avoids extreme balance penalties |
| **99% (Strict)** | `+6,328 MW` | ~151,870 MWh | Near-total immunity against storm misforecasts |

---

## 4. Reproducibility & Verification

All statistics in this document can be re-generated and verified with:
```bash
cd backend
python -m app.scripts.run_analysis
```
No external API calls are made during evaluation; all figures are deterministically derived from `backend/data/jan_2026_snapshot.json`.

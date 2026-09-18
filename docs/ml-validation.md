# Machine Learning Validation & Methodology

This document outlines the machine learning architecture, feature engineering pipeline, chronological evaluation methodology, empirical validation benchmarks, and known limitations for **Campus Resource Autopilot**.

---

## 1. Feature Engineering & Zero-Leakage Guarantee (`app/ml/features.py`)

A common pitfall in operational time-series forecasting is **data leakage**, where features incorporate future observations or include observation $t$ within historical rolling averages. Campus Resource Autopilot enforces strict causal ordering:

### Feature Definitions
1. **Temporal Calendar Features:**
   - `hour` (0–23): Captures diurnal university occupancy patterns.
   - `day_of_week` (0–6): Captures weekday academic schedules vs. weekend reductions.
   - `is_weekend` (0 or 1): Explicit indicator for campus facility shutdowns.
   - `month` (1–12): Captures macro-seasonal variations.

2. **Autoregressive Lags:**
   - $t-1$: Immediate prior period value.
   - $t-2$: Two periods prior value.
   - Seasonal lag:
     - $t-24$ for hourly telemetry (Electricity and Water).
     - $t-7$ for daily telemetry (Waste).

3. **Strict Backward-Looking Rolling Windows:**
   - Rolling Mean and Rolling Standard Deviation are calculated strictly using `shift(1)` past observations (`min_periods=1`):
     $$\text{rolling\_mean}_t = \text{mean}(v_{t-k}, \dots, v_{t-1})$$
   - Observation $t$ is **never** included in its own historical rolling window.
   - Initial window NaN values are filled using backward values or the first valid observation to prevent row dropping and index misalignment.

4. **Multi-Meter Entity Alignment:**
   - When multiple building submeters are present, feature generation groups by `meter_id` (`group_col="meter_id"`), ensuring lag calculations do not bleed across different physical facilities.

---

## 2. Models & Algorithms

### 2.1 Anomaly Detection: Unsupervised Isolation Forest (`app/ml/anomaly_detector.py`)
- **Algorithm:** Scikit-learn `IsolationForest`.
- **Hyperparameters:** `contamination=0.02`, `random_state=42`, `n_estimators=100`.
- **Score Normalization:** The raw decision function (where lower scores denote outliers) is inverted and min-max scaled into a standardized human-interpretable range:
  $$\text{anomaly\_score} \in [0.0, 1.0]$$
  where $1.0$ represents a critical anomalous outlier.
- **Ground-Truth Separation:** Simulation labels (`is_anomaly`) are never passed to the model during training. Predictions are generated unsupervised and stored in `AnomalyPrediction`.

### 2.2 Demand Forecasting: Autoregressive Random Forest (`app/ml/demand_forecaster.py`)
- **Algorithm:** `RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)`.
- **Sampling Frequencies:**
  - **Electricity & Water:** Hourly forecasting (24 steps ahead).
  - **Waste:** Daily forecasting (24 days ahead) logged at 23:00 UTC without fabricating synthetic hourly points.
- **Autoregressive Stepping:** For multi-step forecasts ($t+1, \dots, t+H$), predicted values are dynamically fed back as lag and rolling inputs for subsequent horizons.

---

## 3. Chronological Holdout Validation

To simulate realistic production conditions, models are evaluated using a strict **chronological 80/20 train/test split**:
- **Training Partition (80%):** Days 1 to 24 (historical baseline).
- **Test Partition (20%):** Days 25 to 30 (held-out future telemetry).
- **No Random Shuffling:** Cross-validation with random shuffling is strictly prohibited, as random shuffling leaks temporal structures and artificially inflates accuracy metrics.

---

## 4. Validated Empirical Results

The following benchmarks are generated directly from the 30-day calibrated telemetry dataset across 5 buildings and 15 meters (verified via `scripts/verify_ml.py` and `tests/test_ml.py`):

| Resource | Sampling Frequency | Forecast MAE | Forecast RMSE | Anomaly Precision | Anomaly Recall | Anomaly F1 | Holdout Anomalies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Electricity** | Hourly | **17.34 kWh** | **71.15 kWh** | 0.0000 | 0.0000 | 0.0000 | 0 (See Note 1) |
| **Water** | Hourly | **113.24 L** | **190.12 L** | **0.2083** | **0.2083** | **0.2083** | 72 test readings |
| **Waste** | Daily | **153.79 kg** | **254.99 kg** | **0.2500** | **1.0000** | **0.4000** | 1 test event |

### Empirical Observations & Scientific Disclosure

#### Note 1: Electricity Anomaly Holdout Distribution (F1 = 0.000)
In the 30-day realistic campus seed, the single deliberate electrical surge (a high-draw HVAC chiller malfunction) occurred on **Day 15**. Because Day 15 falls inside the 80% training window (Days 1–24), the 20% future held-out test partition (Days 25–30) contains **exactly 0 ground-truth anomalies**.
- Result: True Positives = 0, False Negatives = 0, False Positives = 73 (normal variations flagged by the unsupervised threshold).
- **Scientific Integrity:** The platform openly reports `Precision: 0.000, Recall: 0.000, F1: 0.000` on the UI and API rather than fabricating fake positive events or manipulating the chronological split to inflate metrics.

#### Note 2: Water Anomaly Performance
Water telemetry contains sustained off-peak night leaks that extend into the test partition. The unsupervised Isolation Forest detects 15 true positive anomaly readings with an F1 score of 0.2083, operating without any labeled training supervision.

#### Note 3: Waste Event Detection
Waste telemetry occurs at daily frequency. A major post-festival surge at the Campus Student Center on Day 28 was correctly flagged with **100% recall** (1 out of 1 event identified).

---

## 5. Known Limitations

1. **Unsupervised Outlier Calibration:** Isolation Forest uses a fixed contamination estimate (`0.02`). In facilities with irregular operational schedules (e.g. exams, athletic events), natural occupancy spikes can produce false positive anomaly alerts.
2. **Short Historical Horizon (30 Days):** The prototype is trained on a 30-day seed. While sufficient for diurnal and day-of-week seasonality, it does not yet capture annual semester cycles (summer term vs. fall semester).
3. **Point Forecasts vs. Prediction Intervals:** The current Random Forest forecaster provides expected point estimates. Probabilistic prediction intervals (quantile regression) are planned for future versions.

# Campus Resource Autopilot — Demonstration Guide (5–7 Minutes)

This walkthrough provides the exact step-by-step demonstration script for presenting **Campus Resource Autopilot** to evaluators, campus administrators, or hackathon judges.

---

## Preparation & Prerequisites

1. **Start Backend Server:**
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
   ```
2. **Start Frontend Server:**
   ```powershell
   cd frontend
   $env:PATH = 'C:\Program Files\nodejs;' + $env:PATH; npm.cmd run dev
   ```
3. **Open Browser:** Navigate to [http://localhost:5173](http://localhost:5173). Verify green "System Online" indicator in the header.

---

## 9-Step Demonstration Flow

| Step | Time | UI Action | What You See | Evaluator / Judge Talk Track |
| :---: | :---: | :--- | :--- | :--- |
| **1** | 0:00 - 0:45 | **Open Dashboard** | Top KPI cards display total electricity (kWh), water (L), and waste (kg) across 5 buildings. | *"Most campus energy tools only show historical reporting. Campus Resource Autopilot is a software-first intelligence platform that moves from consumption data to automated facility action."* |
| **2** | 0:45 - 1:30 | **Select Water Pillar** | Click the **Water** resource tab at the top of the dashboard. | *"Universities rarely have unified IoT submetering on day one. Our system starts software-first with CSV utility logs, and immediately activates anomaly detection, forecasting, and intervention workflows."* |
| **3** | 1:30 - 2:15 | **View Anomaly Alerts** | Scroll to **Anomaly Alerts**; observe top critical anomaly at Science & Engineering Complex. | *"Our unsupervised Isolation Forest flags an off-peak surge of 1,200 L/h against a normal night baseline of 85 L/h (score 0.88), without requiring manual thresholds."* |
| **4** | 2:15 - 3:00 | **View Root-Cause Explanation** | Review **Autopilot Insights** card for the water anomaly. | *"We don't just show an alert; our explanation engine calculates percentage baseline excess (+1,311%) and provides factual, probabilistic diagnostic reasons, such as active plumbing leaks or stuck valves."* |
| **5** | 3:00 - 3:45 | **View Recommendation** | Review **Recommended Facility Action** section on the insight card. | *"A deterministic priority formula scores urgency from 0.0 to 1.0, giving facilities teams specific inspection directives rather than generic advice."* |
| **6** | 3:45 - 4:30 | **Create Facility Intervention** | Click **"Take Action"** on the insight card. | *"With one click, a facility maintenance ticket is created with pre-intervention consumption and the matched diurnal baseline automatically captured."* |
| **7** | 4:30 - 5:15 | **Simulate Impact** | Under **Impact Measurement**, click **"Simulate & Verify"** on the open ticket. | *"In this demonstration mode, the system simulates an 85% excess mitigation. Notice it is clearly badged with 'SIMULATED DEMO IMPACT'—we never claim simulated numbers are physical sensor readings."* |
| **8** | 5:15 - 6:00 | **View Before → After Comparison** | Review verified reduction breakdown and aggregate campus savings. | *"The platform compares post-repair telemetry against the historical baseline: Before was 563.2 L, After is 193.5 L, proving a verified reduction of 369.8 L (-65.7%)."* |
| **9** | 6:00 - 7:00 | **View Demand Forecast & Model Performance** | Inspect **24-Period Demand Forecast Chart** and **Model Performance** section. | *"Our autoregressive Random Forest projects hourly demand 24 periods ahead using zero-leakage lag features. We openly disclose our empirical MAE, RMSE, and holdout distributions."* |

---

## Optional Bonus Demo: CSV Telemetry Ingestion (1–2 min)

To demonstrate the **"Software-first today, IoT-ready tomorrow"** onboarding capability:
1. Scroll to the **Data Ingestion Center** on the dashboard.
2. Click **Download Canonical Template** to download `campus_resource_template.csv`.
3. Upload `data/sample/sample_consumption.csv` (or drag and drop into the dropzone).
4. Observe real-time row validation, duplicate detection, and atomic database insertion without restarting the server.

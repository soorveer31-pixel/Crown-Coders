# Campus Resource Autopilot — Frontend Application

The frontend of **Campus Resource Autopilot** is a responsive, single-page analytics dashboard built with **React 18**, **Vite**, **Tailwind CSS**, and **Recharts**. It provides university facilities teams, sustainability managers, and administrators with actionable insights into electricity, water, and waste consumption.

---

## 1. Features & UI Components

- **Executive Summary Cards (`MetricCard.jsx`):** Live campus consumption aggregates, percentage changes, and status indicators across Electricity, Water, and Waste.
- **Software-First CSV Ingestion Center (`DataIngestion.jsx`):** Drag-and-drop CSV upload zone, real-time validation error reporting, and one-click canonical template download.
- **Anomaly Detection Stream (`AnomalyAlerts.jsx`):** Real-time outlier alerts driven by Isolation Forest inference with normalized anomaly scores ($0.0 - 1.0$) and severity tags.
- **24-Period Demand Forecast Chart (`ForecastChart.jsx`):** Hourly and daily demand forecasts with historical overlap and confidence trends rendered via Recharts.
- **Model Performance & Transparency (`ModelPerformance.jsx`):** Real-time empirical evaluation metrics (MAE, RMSE, Precision, Recall, F1-Score) accompanied by scientific disclosures on holdout partitions.
- **Autopilot Insights Action Center (`AutopilotInsights.jsx`):** Grounded, probabilistic root-cause explanations and prioritized facility directives with one-click intervention dispatch.
- **Closed-Loop Impact Measurement (`ImpactMeasurement.jsx`):** Before vs. After excess reduction analysis, historical baseline comparisons, simulation controls, and verified campus savings summaries.

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── components/           # Modular interface widgets
│   │   ├── Header.jsx        # Navigation bar & backend health status
│   │   ├── MetricCard.jsx    # Top-level resource metric cards
│   │   ├── DataIngestion.jsx # CSV upload & template download interface
│   │   ├── AnomalyAlerts.jsx # Detected anomalies list
│   │   ├── ForecastChart.jsx # Interactive Recharts forecasting component
│   │   ├── ModelPerformance.jsx # Empirical evaluation metrics & holdout notes
│   │   ├── AutopilotInsights.jsx # Root-cause explanations & action directives
│   │   └── ImpactMeasurement.jsx # Verification & savings measurement center
│   ├── pages/
│   │   └── Dashboard.jsx     # Main consolidated operational dashboard
│   ├── services/
│   │   └── api.js            # Native fetch client connecting to FastAPI backend
│   ├── App.jsx               # Root application component with error boundaries
│   ├── main.jsx              # Application DOM mount entry point
│   └── index.css             # Tailwind CSS directives & custom styling
├── index.html                # HTML entry template
├── vite.config.js            # Vite bundler configuration & local dev proxy
├── tailwind.config.js        # Tailwind utility definitions
├── postcss.config.js         # PostCSS processor configuration
├── package.json              # NPM scripts and dependencies
└── README.md                 # This documentation
```

---

## 3. Prerequisites & Setup

### Prerequisites
- Node.js 18+ (Tested with Node.js 20+)
- npm 9+

### Installation

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

---

## 4. Running the Development Server

Start the local Vite development server:

- **PowerShell:**
  ```powershell
  $env:PATH = 'C:\Program Files\nodejs;' + $env:PATH; npm.cmd run dev
  ```
- **Command Prompt (cmd.exe):**
  ```cmd
  set PATH=C:\Program Files\nodejs;%PATH% && npm run dev
  ```
- **macOS / Linux:**
  ```bash
  npm run dev
  ```

Open your browser at [http://localhost:5173](http://localhost:5173).

---

## 5. Building for Production

To create an optimized production build:

- **PowerShell:**
  ```powershell
  $env:PATH = 'C:\Program Files\nodejs;' + $env:PATH; npm.cmd run build
  ```
- **Command Prompt (cmd.exe):**
  ```cmd
  set PATH=C:\Program Files\nodejs;%PATH% && npm run build
  ```
- **macOS / Linux:**
  ```bash
  npm run build
  ```

*The production assets will be output to `dist/` with minified CSS and JavaScript.*

---

## 6. Environment Configuration

By default, the frontend proxies `/api` requests to the FastAPI server running on `http://localhost:8000` via `vite.config.js`.

To point to an external or remote API in production:
```bash
# Create a .env file in frontend/
VITE_API_URL=https://api.yourcampus.edu/api
```

# Campus Resource Autopilot — Backend Service

The backend of **Campus Resource Autopilot** is a high-performance, asynchronous REST microservice built with **FastAPI**, **SQLAlchemy 2.0**, and **Scikit-learn**. It handles data ingestion, telemetry storage, machine learning inference (unsupervised anomaly detection and autoregressive demand forecasting), root-cause explainability, facility recommendations, and post-intervention impact measurement.

---

## 1. Directory Structure

```text
backend/
├── app/
│   ├── api/                  # Modular REST routers
│   │   ├── health.py         # GET /api/health (DB connectivity check)
│   │   ├── resources.py      # GET /api/resources/summary & /history
│   │   ├── ml.py             # GET /api/ml/anomalies, /forecast, /evaluation
│   │   ├── insights.py       # GET /api/insights (Explain & Recommend)
│   │   ├── interventions.py  # POST/GET /api/interventions, GET /api/impact/summary
│   │   └── ingestion.py      # POST /api/ingestion/upload, GET /api/ingestion/template
│   ├── core/                 # Core infrastructure
│   │   ├── config.py         # Application configuration & CORS settings
│   │   └── database.py       # SQLAlchemy engine, SessionLocal, and init_db()
│   ├── database.py           # Convenience proxy re-exporting database.py
│   ├── ml/                   # Machine learning core algorithms
│   │   ├── features.py       # Zero-leakage temporal, lag, and rolling features
│   │   ├── anomaly_detector.py # Unsupervised Isolation Forest engine
│   │   ├── demand_forecaster.py# Autoregressive multi-step regressor
│   │   └── predictor.py      # ResourcePredictor coordinator and evaluation
│   ├── models/               # SQLAlchemy ORM models
│   │   └── campus.py         # Building, ResourceMeter, Reading, Anomaly, Insight, Intervention
│   ├── schemas/              # Pydantic request/response schemas
│   │   ├── ml.py             # Anomaly, Forecast, and Evaluation schemas
│   │   ├── insights.py       # InsightItem, InsightsResponse schemas
│   │   ├── impact.py         # InterventionCreate, Response, ImpactSummary schemas
│   │   └── ingestion.py      # IngestionSummary response schema
│   ├── services/             # Domain business logic
│   │   ├── resource_service.py # Telemetry aggregation & historical slicing
│   │   ├── ml_service.py     # ML extraction & evaluation pipeline
│   │   ├── explanation_service.py # Probabilistic root-cause reasoner
│   │   ├── recommendation_service.py # Priority formula & maintenance directives
│   │   ├── insights_service.py # Closed-loop insights coordinator
│   │   ├── impact_service.py # Baseline calculation, before/after analysis, simulation
│   │   └── ingestion_service.py # CSV parsing, validation, duplicate filtering, atomic DB commits
│   └── main.py               # FastAPI entry point, lifespan, CORS, and router mounting
├── data/                     # Local telemetry storage (excluded from git)
│   ├── campus.db             # Local SQLite database (generated during seed/run)
│   └── sample_campus_upload.csv # Canonical CSV demonstration sample
├── scripts/                  # Verification & operational scripts
│   ├── seed_data.py          # 30-day realistic campus telemetry generator (development reset)
│   ├── verify_demo_flow.py   # 10-step automated end-to-end demo verification
│   ├── verify_ingestion_flow.py # 5-step data ingestion verification
│   ├── verify_impact.py      # Standalone verification for impact calculation
│   └── verify_ml.py          # Standalone verification for ML engines and metrics
├── tests/                    # 58 automated Pytest tests
│   ├── test_api.py           # API endpoints & validation
│   ├── test_impact.py        # Impact calculation & simulation
│   ├── test_ingestion.py     # Ingestion validation, duplicate detection & atomic commits
│   ├── test_insights.py      # Explanation & recommendation engines
│   └── test_ml.py            # Feature engineering, anomaly detection & forecasting
├── .env.example              # Example environment variables
├── requirements.txt          # Python dependencies
└── README.md                 # This documentation
```

---

## 2. Prerequisites & Setup

### Prerequisites
- Python 3.10+ (Tested with Python 3.13)
- PowerShell (Windows) or Bash (macOS/Linux)

### Virtual Environment Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Database Operations: Normal Startup vs. Development Reset

> [!IMPORTANT]
> **Database Safety Distinction:**
> - **Normal Application Startup (`uvicorn app.main:app`)**: Uses SQLAlchemy's `Base.metadata.create_all()`. It initializes tables if they do not exist, but **NEVER drops or clears existing data**.
> - **Development Seed / Reset (`scripts/seed_data.py`)**: An explicit development tool that intentionally drops existing tables, creates 5 buildings, 15 resource meters, and populates 30 days of calibrated hourly and daily readings (7,350 total records with deliberate anomalies). **Only run `seed_data.py` when you intentionally want to reset demo data.**

### Seeding Development Telemetry (One-Time Setup)
```powershell
python scripts/seed_data.py
```
*Expected output: Created 5 buildings, 15 meters, 7,350 consumption readings.*

---

## 4. Starting the Backend Server

Run the development server with auto-reload:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Once running, access:
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 5. Running Automated Tests

The backend includes **58 comprehensive automated tests** using Pytest:

```powershell
pytest -v
```

All 58 tests validate:
- Telemetry ingestion schema validation, row filtering, duplicate detection, and atomic commits (`test_ingestion.py`).
- Zero future data leakage in lag and rolling feature calculations (`test_ml.py`).
- Isolation Forest anomaly scoring and Random Forest multi-step demand forecasting (`test_ml.py`).
- Probabilistic root-cause explanations and priority-weighted facility recommendations (`test_insights.py`).
- Historical baseline matching, before/after excess reductions, and intervention tracking (`test_impact.py`).
- API status codes, sanitized error responses, and parameter edge cases (`test_api.py`).

---

## 6. Running Verification Scripts

Run standalone end-to-end verification scripts:

```powershell
# 10-step full demonstration flow verification
python scripts/verify_demo_flow.py

# Data ingestion and template download verification
python scripts/verify_ingestion_flow.py

# Machine learning model benchmarks verification
python scripts/verify_ml.py

# Impact measurement and baseline calculation verification
python scripts/verify_impact.py
```

---

## 7. Key API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health and database connectivity ping |
| `GET` | `/api/resources/summary` | Campus-wide consumption totals and current rates |
| `GET` | `/api/resources/history?resource=water&range=7d` | Historical telemetry time series (7d or 30d) |
| `GET` | `/api/ml/anomalies?resource=water&range=7d` | Unsupervised Isolation Forest detected anomalies |
| `GET` | `/api/ml/forecast?resource=electricity&horizon=24` | Multi-step autoregressive demand forecast |
| `GET` | `/api/ml/evaluation?resource=electricity` | Out-of-sample empirical model performance metrics |
| `GET` | `/api/insights?resource=water&range=7d` | Root-cause explanations & prioritized recommendations |
| `POST` | `/api/interventions` | Create facility intervention ticket from an insight |
| `POST` | `/api/interventions/{id}/simulate` | Simulate 85% excess mitigation for live demonstration |
| `POST` | `/api/interventions/{id}/complete` | Finalize intervention status and lock impact values |
| `GET` | `/api/interventions` | List all planned, in-progress, and completed interventions |
| `GET` | `/api/impact/summary` | Aggregate campus resource savings and active interventions |
| `POST` | `/api/ingestion/upload` | Upload and validate canonical telemetry CSV |
| `GET` | `/api/ingestion/template` | Download canonical CSV template |

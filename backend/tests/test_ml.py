"""Milestone 3 Automated Tests - Machine Learning Layer.

Verifies:
1. Feature engineering (no future data leakage, proper lag and rolling shifts)
2. Anomaly detection output (predicted_anomaly bool, normalized anomaly_score)
3. Forecast output (24-period future projection, non-negative values)
4. Waste daily frequency preservation
5. Forecast horizon parameter validation
6. Invalid resource handling (HTTP 400)
7. Evaluation metrics calculation (MAE, RMSE, Precision, Recall, F1)
8. GET /api/ml/anomalies endpoint schema and filtering
9. GET /api/ml/forecast endpoint schema and 24-step projection
10. Graceful handling of empty/small database
"""

import pytest
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.campus import Building, ResourceMeter, ConsumptionReading
from app.ml.features import (
    add_temporal_features,
    add_lag_and_rolling_features,
    extract_features,
    get_anomaly_feature_columns,
    get_forecast_feature_columns,
)
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.demand_forecaster import DemandForecaster
from app.services.ml_service import MLService

# Isolated in-memory SQLite engine for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates tables before each test and cleans up afterward."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient using the isolated database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def populated_db(db_session):
    """Populates the test database with realistic synthetic readings including an anomaly."""
    b = Building(name="Engineering Hall", type="Academic", sqft=60000)
    db_session.add(b)
    db_session.commit()

    m_elec = ResourceMeter(building_id=b.id, resource_type="electricity", unit="kWh")
    m_water = ResourceMeter(building_id=b.id, resource_type="water", unit="L")
    m_waste = ResourceMeter(building_id=b.id, resource_type="waste", unit="kg")
    db_session.add_all([m_elec, m_water, m_waste])
    db_session.commit()

    start_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    readings = []

    # 14 days of hourly electricity & water (336 hours)
    for h in range(336):
        ts = start_time + timedelta(hours=h)
        base_elec = 100.0 + 30.0 * np.sin(h * np.pi / 12)
        base_water = 200.0 + 50.0 * np.sin(h * np.pi / 12)
        is_leak = (200 <= h <= 210)
        water_val = base_water + (500.0 if is_leak else 0.0)

        readings.append(ConsumptionReading(meter_id=m_elec.id, timestamp=ts, value=round(base_elec, 2), is_anomaly=False))
        readings.append(ConsumptionReading(meter_id=m_water.id, timestamp=ts, value=round(water_val, 2), is_anomaly=is_leak))

    # 14 days of daily waste
    for d in range(14):
        ts = (start_time + timedelta(days=d)).replace(hour=23)
        readings.append(ConsumptionReading(meter_id=m_waste.id, timestamp=ts, value=150.0, is_anomaly=False))

    db_session.add_all(readings)
    db_session.commit()
    return db_session


# 1. Test Feature Engineering & No Data Leakage
def test_feature_engineering_no_future_leakage():
    """Verifies that rolling features do NOT use current or future observations."""
    timestamps = [datetime(2026, 8, 1, h, 0, 0) for h in range(10)]
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    df = pd.DataFrame({"timestamp": timestamps, "value": values})

    features = extract_features(df, resource_type="electricity")

    # Step 0: lag_1 is filled from initial value
    assert "lag_1" in features.columns
    assert "rolling_mean" in features.columns

    # Step 1: past value was only Step 0 (value=10.0)
    assert features.loc[1, "lag_1"] == 10.0
    assert features.loc[1, "rolling_mean"] == 10.0

    # Step 2: rolling mean must only observe past values [10, 20], so mean=15.0. It MUST NOT include 30.0!
    assert features.loc[2, "lag_1"] == 20.0
    assert features.loc[2, "rolling_mean"] == 15.0

    # Check temporal features
    assert features.loc[5, "hour"] == 5
    assert "is_weekend" in features.columns


# 2. Test Anomaly Detection Output Structure
def test_anomaly_detection_output():
    """Verifies Isolation Forest returns boolean predictions and [0, 1] normalized scores."""
    base_ts = datetime(2026, 8, 1, 0, 0, 0)
    timestamps = [base_ts + timedelta(hours=h) for h in range(50)]
    values = [50.0 + np.random.normal(0, 2) for _ in range(50)]
    values[25] = 500.0  # Obvious spike outlier
    df = pd.DataFrame({"timestamp": timestamps, "value": values, "is_anomaly": False})
    df.loc[25, "is_anomaly"] = True

    detector = AnomalyDetector("electricity", contamination=0.04)
    detector.fit(df)
    preds, scores = detector.predict(df)

    assert len(preds) == 50
    assert len(scores) == 50
    assert isinstance(preds[0], (bool, np.bool_))
    assert 0.0 <= scores.min() <= 1.0
    assert 0.0 <= scores.max() <= 1.0


# 3. Test Demand Forecaster Output
def test_demand_forecaster_output():
    """Verifies that forecasting generates requested horizon periods with valid future timestamps."""
    base_ts = datetime(2026, 8, 1, 0, 0, 0)
    timestamps = [base_ts + timedelta(hours=h) for h in range(100)]
    values = [100.0 + 20.0 * np.sin(h * np.pi / 12) for h in range(100)]
    df = pd.DataFrame({"timestamp": timestamps, "value": values})


    forecaster = DemandForecaster("electricity")
    forecaster.fit(df)
    forecast = forecaster.forecast(df, horizon=24)

    assert len(forecast) == 24
    last_hist_ts = timestamps[-1]
    first_forecast_ts = datetime.fromisoformat(forecast[0]["timestamp"])
    assert first_forecast_ts > last_hist_ts
    assert all(f["predicted_value"] >= 0.0 for f in forecast)
    assert all(f["resource"] == "electricity" for f in forecast)
    assert all(f["unit"] == "kWh" for f in forecast)


# 4. Test Waste Daily Frequency
def test_waste_daily_frequency():
    """Verifies that waste forecasting respects daily intervals (24-hour steps)."""
    timestamps = [datetime(2026, 8, d, 23, 0, 0) for d in range(1, 20)]
    values = [200.0 + np.random.normal(0, 10) for _ in range(19)]
    df = pd.DataFrame({"timestamp": timestamps, "value": values})

    forecaster = DemandForecaster("waste")
    forecaster.fit(df)
    forecast = forecaster.forecast(df, horizon=5)

    assert len(forecast) == 5
    for i in range(len(forecast) - 1):
        t1 = datetime.fromisoformat(forecast[i]["timestamp"])
        t2 = datetime.fromisoformat(forecast[i + 1]["timestamp"])
        delta = t2 - t1
        assert delta == timedelta(days=1), f"Expected 1 day difference, got {delta}"


# 5. Test Forecast Horizon Validation
def test_forecast_horizon_validation(client, populated_db):
    """Verifies that invalid horizon values produce HTTP 400."""
    # Negative horizon
    r1 = client.get("/api/ml/forecast?resource=electricity&horizon=-5")
    assert r1.status_code == 422 or r1.status_code == 400

    # Zero horizon
    r2 = client.get("/api/ml/forecast?resource=electricity&horizon=0")
    assert r2.status_code == 422 or r2.status_code == 400

    # Exceeding maximum allowed horizon (> 168)
    r3 = client.get("/api/ml/forecast?resource=electricity&horizon=500")
    assert r3.status_code == 422 or r3.status_code == 400


# 6. Test Invalid Resource Handling
def test_invalid_resource_handling(client, populated_db):
    """Verifies that unsupported resources return HTTP 400 across all ML endpoints."""
    bad_resource = "unsupported_resource"

    r_anom = client.get(f"/api/ml/anomalies?resource={bad_resource}")
    assert r_anom.status_code == 400
    assert "Invalid resource" in r_anom.json()["detail"]

    r_fc = client.get(f"/api/ml/forecast?resource={bad_resource}")
    assert r_fc.status_code == 400
    assert "Invalid resource" in r_fc.json()["detail"]

    r_eval = client.get(f"/api/ml/evaluation?resource={bad_resource}")
    assert r_eval.status_code == 400
    assert "Invalid resource" in r_eval.json()["detail"]


# 7. Test Evaluation Metrics Calculation
def test_evaluation_metrics_calculation(populated_db):
    """Verifies mathematical validity of evaluation metrics (MAE, RMSE, Precision, Recall, F1)."""
    service = MLService(populated_db)
    metrics = service.get_evaluation("water")

    assert "forecast" in metrics
    assert "anomaly_detection" in metrics
    assert metrics["forecast"]["mae"] >= 0.0
    assert metrics["forecast"]["rmse"] >= 0.0

    anom = metrics["anomaly_detection"]
    assert 0.0 <= anom["precision"] <= 1.0
    assert 0.0 <= anom["recall"] <= 1.0
    assert 0.0 <= anom["f1"] <= 1.0
    assert anom["actual_anomalies"] >= 0
    assert anom["true_positives"] >= 0


# 8. Test API GET /api/ml/anomalies
def test_api_anomalies_endpoint(client, populated_db):
    """Verifies the GET /api/ml/anomalies endpoint returns correct JSON structure."""
    response = client.get("/api/ml/anomalies?resource=water&range=7d")
    assert response.status_code == 200
    data = response.json()

    assert data["resource"] == "water"
    assert data["unit"] == "L"
    assert data["range"] == "7d"
    assert "total_anomalies" in data
    assert isinstance(data["anomalies"], list)

    if data["anomalies"]:
        first = data["anomalies"][0]
        assert "timestamp" in first
        assert "value" in first
        assert "anomaly_score" in first
        assert "predicted_anomaly" in first
        assert first["predicted_anomaly"] is True
        assert 0.0 <= first["anomaly_score"] <= 1.0


# 9. Test API GET /api/ml/forecast
def test_api_forecast_endpoint(client, populated_db):
    """Verifies the GET /api/ml/forecast endpoint generates valid 24-step predictions."""
    response = client.get("/api/ml/forecast?resource=electricity&horizon=24")
    assert response.status_code == 200
    data = response.json()

    assert data["resource"] == "electricity"
    assert data["unit"] == "kWh"
    assert data["horizon"] == 24
    assert data["frequency"] == "hourly"
    assert len(data["predictions"]) == 24
    assert data["predictions"][0]["resource"] == "electricity"
    assert data["predictions"][0]["predicted_value"] >= 0.0


# 10. Test Empty Database Handling
def test_empty_database_behavior(client):
    """Verifies that ML endpoints handle an empty database gracefully without 500 errors."""
    r_anom = client.get("/api/ml/anomalies?resource=electricity&range=7d")
    assert r_anom.status_code == 200
    assert r_anom.json()["total_anomalies"] == 0
    assert r_anom.json()["anomalies"] == []

    r_fc = client.get("/api/ml/forecast?resource=electricity&horizon=24")
    assert r_fc.status_code == 200
    assert r_fc.json()["predictions"] == []

    r_eval = client.get("/api/ml/evaluation?resource=electricity")
    assert r_eval.status_code == 200
    assert r_eval.json()["forecast"]["mae"] == 0.0
    assert r_eval.json()["anomaly_detection"]["precision"] == 0.0

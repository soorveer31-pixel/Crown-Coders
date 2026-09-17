"""Milestone 4A Automated Tests - Explain & Recommendation Engine.

Verifies:
1. Water anomaly explanation (off-peak vs peak, pipe leak vs active draw)
2. Electricity anomaly explanation (unoccupied baseload override vs peak surge)
3. Waste anomaly explanation (severe accumulation vs normal variance)
4. Percentage deviation calculation accuracy and edge-case handling
5. Priority calculation formula compliance and bound validation [0.0, 1.0]
6. High and Critical severity recommendations
7. Medium and Low severity recommendations
8. Forecast-based proactive risk insight generation
9. Invalid API parameter handling (HTTP 400)
10. Empty dataset graceful handling without errors
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.campus import Building, ResourceMeter, ConsumptionReading, Insight
from app.services.explanation_service import ExplanationService
from app.services.recommendation_service import RecommendationService
from app.services.insights_service import InsightsService

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session per test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient connected to the isolated database session."""
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
    """Populates database with realistic readings across all 3 streams with anomalies."""
    b1 = Building(name="Evergreen Residence Hall", type="Residential", sqft=80000)
    b2 = Building(name="Science Complex", type="Academic", sqft=100000)
    db_session.add_all([b1, b2])
    db_session.commit()

    m_water = ResourceMeter(building_id=b1.id, resource_type="water", unit="L")
    m_elec = ResourceMeter(building_id=b2.id, resource_type="electricity", unit="kWh")
    m_waste = ResourceMeter(building_id=b2.id, resource_type="waste", unit="kg")
    db_session.add_all([m_water, m_elec, m_waste])
    db_session.commit()

    start_ts = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    readings = []

    # 14 days of hourly data (336 hours)
    for h in range(336):
        ts = start_ts + timedelta(hours=h)
        # Water leak at step 200-205 (off-peak night)
        is_leak = (200 <= h <= 205)
        water_val = 1200.0 if is_leak else 250.0
        readings.append(ConsumptionReading(meter_id=m_water.id, timestamp=ts, value=water_val, is_anomaly=is_leak))

        # Electricity surge at step 100
        is_elec_spike = (h == 100)
        elec_val = 600.0 if is_elec_spike else 150.0
        readings.append(ConsumptionReading(meter_id=m_elec.id, timestamp=ts, value=elec_val, is_anomaly=is_elec_spike))

    # 14 days of daily waste
    for d in range(14):
        ts = (start_ts + timedelta(days=d)).replace(hour=23)
        is_waste_spike = (d == 12)
        waste_val = 1800.0 if is_waste_spike else 200.0
        readings.append(ConsumptionReading(meter_id=m_waste.id, timestamp=ts, value=waste_val, is_anomaly=is_waste_spike))

    db_session.add_all(readings)
    db_session.commit()
    return db_session


# 1. Test Water Anomaly Explanation
def test_water_anomaly_explanation():
    """Verifies deterministic explanation for off-peak water leak vs peak draw."""
    ts_night = datetime(2026, 8, 1, 3, 30, 0)  # 03:30 AM (off-peak night)
    expl_night = ExplanationService.explain_anomaly(
        resource_type="water",
        observed_value=1200.0,
        expected_value=200.0,
        timestamp=ts_night,
        anomaly_score=0.85,
        building_name="Evergreen Residence Hall",
        unit="L",
    )
    assert expl_night["is_off_peak"] is True
    assert expl_night["deviation_percent"] == 500.0
    assert "plumbing leak" in expl_night["reason"].lower() or "pipe" in expl_night["reason"].lower()

    ts_day = datetime(2026, 8, 5, 14, 0, 0)  # Wednesday 14:00 (active weekday hours)
    expl_day = ExplanationService.explain_anomaly(
        resource_type="water",
        observed_value=800.0,
        expected_value=300.0,
        timestamp=ts_day,
        anomaly_score=0.60,
        building_name="Dining Commons",
        unit="L",
    )
    assert expl_day["is_off_peak"] is False

    assert "cooling tower" in expl_day["reason"].lower() or "fixture" in expl_day["reason"].lower()


# 2. Test Electricity Anomaly Explanation
def test_electricity_anomaly_explanation():
    """Verifies deterministic explanation for off-peak vs operational electricity surges."""
    ts_weekend_night = datetime(2026, 8, 2, 2, 0, 0)  # Sunday 02:00 AM (off-peak)
    expl_off = ExplanationService.explain_anomaly(
        resource_type="electricity",
        observed_value=450.0,
        expected_value=100.0,
        timestamp=ts_weekend_night,
        anomaly_score=0.88,
        building_name="Science Complex",
        unit="kWh",
    )
    assert expl_off["is_off_peak"] is True
    assert "unoccupied" in expl_off["reason"].lower() or "baseload" in expl_off["reason"].lower()

    ts_weekday_noon = datetime(2026, 8, 5, 12, 0, 0)  # Wednesday 12:00 (peak)
    expl_peak = ExplanationService.explain_anomaly(
        resource_type="electricity",
        observed_value=600.0,
        expected_value=350.0,
        timestamp=ts_weekday_noon,
        anomaly_score=0.70,
        building_name="Science Complex",
        unit="kWh",
    )
    assert "peak" in expl_peak["reason"].lower() or "operating" in expl_peak["reason"].lower()


# 3. Test Waste Anomaly Explanation
def test_waste_anomaly_explanation():
    """Verifies explanation of severe waste generation surges."""
    ts = datetime(2026, 8, 10, 23, 0, 0)
    expl = ExplanationService.explain_anomaly(
        resource_type="waste",
        observed_value=1500.0,
        expected_value=300.0,
        timestamp=ts,
        anomaly_score=0.92,
        building_name="Campus Student Center",
        unit="kg",
    )
    assert expl["deviation_percent"] == 400.0
    assert "event" in expl["reason"].lower() or "festival" in expl["reason"].lower()


# 4. Test Percentage Deviation Calculation
def test_percentage_deviation_calculation():
    """Verifies mathematical correctness of percentage deviation."""
    ts = datetime(2026, 8, 1, 10, 0, 0)
    # 100 observed vs 50 expected -> +100%
    r1 = ExplanationService.explain_anomaly("electricity", 100.0, 50.0, ts, 0.5, "Hall", "kWh")
    assert r1["deviation_percent"] == 100.0
    assert r1["absolute_deviation"] == 50.0

    # 150 observed vs 100 expected -> +50%
    r2 = ExplanationService.explain_anomaly("electricity", 150.0, 100.0, ts, 0.5, "Hall", "kWh")
    assert r2["deviation_percent"] == 50.0
    assert r2["absolute_deviation"] == 50.0


# 5. Test Priority Calculation Formula & Bounds
def test_priority_calculation_formula():
    """Verifies priority score formula adheres to documented weights and bounds [0.0, 1.0]."""
    # Max condition: anomaly_score=1.0, deviation=300% (capped at 200%), off_peak=True, water (0.90)
    # Formula: 0.40(1.0) + 0.30(1.0) + 0.20(1.0) + 0.10(0.90) = 0.40 + 0.30 + 0.20 + 0.09 = 0.99
    p_max = RecommendationService.calculate_priority(
        anomaly_score=1.0,
        deviation_percent=300.0,
        is_off_peak=True,
        resource_type="water",
    )
    assert 0.95 <= p_max["priority_score"] <= 1.0
    assert p_max["severity"] == "CRITICAL"

    # Minimum condition: anomaly_score=0.0, deviation=0%, off_peak=False, waste (0.70)
    # Formula: 0.40(0) + 0.30(0) + 0.20(0) + 0.10(0.70) = 0.07
    p_min = RecommendationService.calculate_priority(
        anomaly_score=0.0,
        deviation_percent=0.0,
        is_off_peak=False,
        resource_type="waste",
    )
    assert 0.0 <= p_min["priority_score"] <= 0.15
    assert p_min["severity"] == "LOW"


# 6. Test High / Critical Severity Recommendation
def test_high_severity_recommendation():
    """Verifies high and critical priority recommendations contain actionable directives."""
    ts = datetime(2026, 8, 1, 3, 0, 0)
    rec = RecommendationService.generate_anomaly_recommendation(
        resource_type="water",
        observed_value=1500.0,
        expected_value=200.0,
        timestamp=ts,
        anomaly_score=0.90,
        building_name="Evergreen Residence Hall",
        unit="L",
    )
    assert rec["severity"] in ["CRITICAL", "HIGH"]
    assert rec["priority_score"] >= 0.65
    assert "shut-off" in rec["recommended_action"].lower() or "isolate" in rec["recommended_action"].lower()
    assert "leak" in rec["title"].lower() or "pipe" in rec["title"].lower()


# 7. Test Medium / Low Severity Recommendation
def test_medium_low_recommendation():
    """Verifies medium and low severity recommendation generation."""
    ts = datetime(2026, 8, 1, 14, 0, 0)
    rec = RecommendationService.generate_anomaly_recommendation(
        resource_type="waste",
        observed_value=120.0,
        expected_value=100.0,
        timestamp=ts,
        anomaly_score=0.35,
        building_name="Library",
        unit="kg",
    )
    assert rec["severity"] in ["LOW", "MEDIUM"]
    assert rec["priority_score"] < 0.65
    assert len(rec["recommended_action"]) > 10


# 8. Test Forecast-Based Proactive Risk Insight
def test_forecast_based_proactive_insight():
    """Verifies proactive risk insight triggered when forecast exceeds historical baseline by >20%."""
    pred_point = {
        "timestamp": "2026-08-15T14:00:00",
        "predicted_value": 850.0,
        "resource": "electricity",
        "unit": "kWh",
    }
    baseline = 500.0  # +70% excess

    risk = RecommendationService.generate_forecast_risk_insight(
        resource_type="electricity",
        predicted_point=pred_point,
        historical_baseline=baseline,
        threshold_multiplier=1.20,
    )
    assert risk is not None
    assert risk["type"] == "forecast_risk"
    assert "peak" in risk["title"].lower() or "spike" in risk["title"].lower()
    assert risk["deviation_percent"] == 70.0
    assert "pre-cool" in risk["recommended_action"].lower() or "thermostat" in risk["recommended_action"].lower()

    # Below threshold -> no risk insight
    no_risk = RecommendationService.generate_forecast_risk_insight(
        resource_type="electricity",
        predicted_point={"timestamp": "2026-08-15T14:00:00", "predicted_value": 520.0, "unit": "kWh"},
        historical_baseline=500.0,
        threshold_multiplier=1.20,
    )
    assert no_risk is None


# 9. Test Invalid API Parameters
def test_invalid_api_parameters(client, populated_db):
    """Verifies that invalid resource or range queries return HTTP 400."""
    r_res = client.get("/api/insights?resource=invalid_fuel")
    assert r_res.status_code == 400
    assert "Invalid resource" in r_res.json()["detail"]

    r_range = client.get("/api/insights?range=180d")
    assert r_range.status_code == 400
    assert "Invalid range" in r_range.json()["detail"]


# 10. Test Empty Dataset Graceful Handling
def test_empty_dataset_behavior(client):
    """Verifies empty database does not crash the insights API."""
    response = client.get("/api/insights?resource=water&range=7d")
    assert response.status_code == 200
    data = response.json()
    assert data["total_insights"] == 0
    assert data["detected_issues_count"] == 0
    assert data["upcoming_risks_count"] == 0
    assert data["insights"] == []

"""Comprehensive automated test suite for Impact & Savings Measurement (Milestone 4B)."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.campus import Building, ResourceMeter, ConsumptionReading, Insight, Intervention
from app.services.impact_service import ImpactService


@pytest.fixture
def in_memory_db():
    """Provides an isolated in-memory SQLite session with schema initialized."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def populated_db(in_memory_db):
    """Populates database with sample building, meters, readings, and insights."""
    b = Building(id=1, name="Science & Engineering Complex", type="Academic", sqft=85000)
    in_memory_db.add(b)

    m_elec = ResourceMeter(id=1, building_id=1, resource_type="electricity", unit="kWh")
    m_water = ResourceMeter(id=2, building_id=1, resource_type="water", unit="L")
    m_waste = ResourceMeter(id=3, building_id=1, resource_type="waste", unit="kg")
    in_memory_db.add_all([m_elec, m_water, m_waste])

    # Add historical baseline readings (normal, non-anomalous)
    for hour in range(24):
        in_memory_db.add(ConsumptionReading(
            meter_id=2,
            timestamp=datetime(2026, 8, 10, hour, 0, 0),
            value=120.0 + (hour * 2.0),
            is_anomaly=False,
        ))
        in_memory_db.add(ConsumptionReading(
            meter_id=1,
            timestamp=datetime(2026, 8, 10, hour, 0, 0),
            value=50.0 + (hour * 1.5),
            is_anomaly=False,
        ))

    # Add insight
    ins = Insight(
        id=1,
        resource_type="water",
        building_name="Science & Engineering Complex",
        timestamp=datetime(2026, 8, 10, 14, 0, 0),
        insight_type="anomaly",
        severity="HIGH",
        priority_score=0.75,
        title="High Water Leak Detected",
        explanation="Water consumption exceeds diurnal baseline by 300%.",
        recommendation="Inspect cooling tower float valve.",
        recommended_action="Dispatch plumbing team to inspect zone valves.",
        observed_value=500.0,
        expected_value=150.0,
    )
    in_memory_db.add(ins)
    in_memory_db.commit()
    return in_memory_db


@pytest.fixture
def client(populated_db):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield populated_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# 1. Baseline calculation
def test_baseline_calculation(populated_db):
    service = ImpactService(populated_db)
    baseline = service.calculate_comparable_baseline(
        resource_type="water",
        building_id=1,
        event_time=datetime(2026, 8, 10, 14, 0, 0),
    )
    assert baseline > 0
    # Expected around 120 + 14*2 = 148
    assert 130.0 <= baseline <= 160.0


# 2. Positive savings calculation
def test_positive_savings_calculation():
    metrics = ImpactService.calculate_impact_metrics(
        before_value=500.0,
        after_value=200.0,
        baseline_value=150.0,
    )
    assert metrics["absolute_reduction"] == 300.0
    assert metrics["estimated_savings"] == 300.0
    assert metrics["savings_percentage"] == 60.0
    assert metrics["excess_before"] == 350.0
    assert metrics["excess_after"] == 50.0
    assert metrics["excess_reduction"] == 300.0
    assert metrics["impact_status_message"] == "Improvement observed"


# 3. Increased consumption case (Negative savings guard)
def test_increased_consumption_case():
    metrics = ImpactService.calculate_impact_metrics(
        before_value=300.0,
        after_value=400.0,
        baseline_value=150.0,
    )
    assert metrics["absolute_reduction"] == -100.0
    # Must NOT report negative savings as positive savings!
    assert metrics["estimated_savings"] == 0.0
    assert metrics["savings_percentage"] == 0.0
    assert metrics["impact_status_message"] == "Consumption increased"


# 4. Zero division protection
def test_zero_division_protection():
    metrics = ImpactService.calculate_impact_metrics(
        before_value=0.0,
        after_value=0.0,
        baseline_value=0.0,
    )
    assert metrics["savings_percentage"] == 0.0
    assert metrics["estimated_savings"] == 0.0


# 5. Simulated intervention engine
def test_simulated_intervention_engine():
    # Before = 500, Baseline = 150, Excess = 350
    # Default factor 0.85 -> After = 150 + (1 - 0.85)*350 = 150 + 52.5 = 202.5
    sim_after = ImpactService.simulate_after_value(
        before_value=500.0,
        baseline_value=150.0,
        simulated_reduction_factor=0.85,
    )
    assert sim_after == 202.5
    assert sim_after < 500.0
    assert sim_after >= 150.0


# 6. Measured intervention structure
def test_measured_intervention_structure(populated_db):
    service = ImpactService(populated_db)
    itv = service.create_intervention(insight_id=1, action="Manual valve repair")
    assert itv.status == "PLANNED"

    completed = service.complete_intervention(intervention_id=itv.id, after_value=160.0)
    assert completed.status == "COMPLETED"
    assert completed.measurement_type == "MEASURED"
    assert completed.after_value == 160.0
    assert completed.estimated_savings == 340.0  # 500 - 160


# 7. Intervention creation API
def test_api_create_intervention(client):
    response = client.post("/api/interventions", json={"insight_id": 1, "action": "Fix cooling valve"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["insight_id"] == 1
    assert data["status"] == "PLANNED"
    assert data["resource_type"] == "water"
    assert data["building_name"] == "Science & Engineering Complex"
    assert data["before_value"] == 500.0
    assert data["baseline_value"] == 150.0
    assert data["unit"] == "L"


# 8. Intervention simulation API
def test_api_simulate_intervention(client):
    create_res = client.post("/api/interventions", json={"insight_id": 1})
    itv_id = create_res.json()["id"]

    sim_res = client.post(f"/api/interventions/{itv_id}/simulate", json={"simulated_reduction_factor": 0.85})
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["status"] == "COMPLETED"
    assert data["measurement_type"] == "SIMULATED"
    assert data["after_value"] == 202.5
    assert data["estimated_savings"] == 297.5  # 500 - 202.5
    assert data["savings_percentage"] == 59.5  # 297.5 / 500 * 100
    assert data["impact_status_message"] == "Improvement observed"


# 9. Intervention completion API
def test_api_complete_intervention(client):
    create_res = client.post("/api/interventions", json={"insight_id": 1})
    itv_id = create_res.json()["id"]

    comp_res = client.post(f"/api/interventions/{itv_id}/complete?after_value=175.0")
    assert comp_res.status_code == 200
    data = comp_res.json()
    assert data["status"] == "COMPLETED"
    assert data["measurement_type"] == "MEASURED"
    assert data["after_value"] == 175.0
    assert data["estimated_savings"] == 325.0


# 10. Intervention history listing API
def test_api_list_interventions(client):
    client.post("/api/interventions", json={"insight_id": 1})
    res = client.get("/api/interventions")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    # Filter by resource
    res_water = client.get("/api/interventions?resource=water")
    assert res_water.status_code == 200
    assert len(res_water.json()) >= 1

    res_waste = client.get("/api/interventions?resource=waste")
    assert res_waste.status_code == 200
    assert len(res_waste.json()) == 0


# 11. Single intervention details API
def test_api_get_intervention_by_id(client):
    create_res = client.post("/api/interventions", json={"insight_id": 1})
    itv_id = create_res.json()["id"]

    detail_res = client.get(f"/api/interventions/{itv_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == itv_id


# 12. Impact summary endpoint API
def test_api_impact_summary(client):
    create_res = client.post("/api/interventions", json={"insight_id": 1})
    itv_id = create_res.json()["id"]
    client.post(f"/api/interventions/{itv_id}/simulate")

    summary_res = client.get("/api/impact/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()

    assert "water" in summary
    assert "electricity" in summary
    assert "waste" in summary
    assert summary["water"]["unit"] == "L"
    assert summary["electricity"]["unit"] == "kWh"
    assert summary["waste"]["unit"] == "kg"
    assert summary["water"]["total_estimated_savings"] > 0
    assert summary["water"]["completed_interventions"] == 1
    assert summary["overall_measurement_type"] == "SIMULATED"
    assert "SIMULATED DEMO IMPACT" in summary["disclaimer"]


# 13. Resource-specific units preservation
def test_resource_specific_units():
    assert ImpactService.RESOURCE_UNITS["water"] == "L"
    assert ImpactService.RESOURCE_UNITS["electricity"] == "kWh"
    assert ImpactService.RESOURCE_UNITS["waste"] == "kg"


# 14. Insight/intervention relationship and 404 validation
def test_insight_validation_and_404(client):
    # Nonexistent insight ID
    bad_res = client.post("/api/interventions", json={"insight_id": 9999})
    assert bad_res.status_code == 404
    assert "not found" in bad_res.json()["detail"].lower()

    # Nonexistent intervention ID
    bad_itv = client.get("/api/interventions/9999")
    assert bad_itv.status_code == 404

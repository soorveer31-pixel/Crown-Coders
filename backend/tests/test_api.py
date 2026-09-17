"""Backend API and Service Tests for Milestone 2."""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.campus import Building, ResourceMeter, ConsumptionReading

# In-memory SQLite engine isolated for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates tables before each test and drops them afterward."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Overrides get_db dependency to use the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_database_initialization(db_session):
    """Test 1: Verifies database tables are created with proper schemas."""
    # Ensure tables exist by querying them directly
    building_count = db_session.query(Building).count()
    meter_count = db_session.query(ResourceMeter).count()
    reading_count = db_session.query(ConsumptionReading).count()
    assert building_count == 0
    assert meter_count == 0
    assert reading_count == 0


def test_health_check_connected(client):
    """Test 2: GET /api/health returns database: connected via SELECT 1."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert data["service"] == "campus-resource-autopilot-backend"


def test_empty_database_behavior(client):
    """Test 3: Summary and history endpoints behave cleanly on an empty database."""
    # Summary on empty DB returns zeroed metrics rather than crashing
    summary_resp = client.get("/api/resources/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    for res in ["electricity", "water", "waste"]:
        assert res in summary
        assert summary[res]["current"] == 0.0
        assert summary[res]["average"] == 0.0
        assert summary[res]["total"] == 0.0

    # History on empty DB returns empty data array
    history_resp = client.get("/api/resources/history?resource=electricity&range=7d")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert history["resource"] == "electricity"
    assert history["data"] == []


def test_resource_summary_with_data(client, db_session):
    """Test 4: GET /api/resources/summary calculates correct totals and averages."""
    # Seed minimal test data
    b = Building(name="Test Hall", type="Academic", sqft=50000)
    db_session.add(b)
    db_session.commit()

    m_elec = ResourceMeter(building_id=b.id, resource_type="electricity", unit="kWh")
    m_water = ResourceMeter(building_id=b.id, resource_type="water", unit="L")
    m_waste = ResourceMeter(building_id=b.id, resource_type="waste", unit="kg")
    db_session.add_all([m_elec, m_water, m_waste])
    db_session.commit()

    now = datetime.now(timezone.utc)
    readings = [
        ConsumptionReading(meter_id=m_elec.id, timestamp=now - timedelta(hours=2), value=100.0),
        ConsumptionReading(meter_id=m_elec.id, timestamp=now - timedelta(hours=1), value=150.0),
        ConsumptionReading(meter_id=m_elec.id, timestamp=now, value=200.0),
        ConsumptionReading(meter_id=m_water.id, timestamp=now, value=500.0),
        ConsumptionReading(meter_id=m_waste.id, timestamp=now, value=80.0),
    ]
    db_session.add_all(readings)
    db_session.commit()

    response = client.get("/api/resources/summary")
    assert response.status_code == 200
    data = response.json()

    # Electricity: latest=200, total=450, avg=(100+150+200)/3 = 150
    assert data["electricity"]["current"] == 200.0
    assert data["electricity"]["total"] == 450.0
    assert data["electricity"]["average"] == 150.0
    assert data["electricity"]["unit"] == "kWh"

    # Water
    assert data["water"]["current"] == 500.0
    assert data["water"]["total"] == 500.0
    assert data["water"]["unit"] == "L"

    # Waste
    assert data["waste"]["current"] == 80.0
    assert data["waste"]["total"] == 80.0
    assert data["waste"]["unit"] == "kg"


def test_resource_history_with_data(client, db_session):
    """Test 5: GET /api/resources/history returns sorted time-series points."""
    b = Building(name="Test Hall", type="Academic", sqft=50000)
    db_session.add(b)
    db_session.commit()

    m = ResourceMeter(building_id=b.id, resource_type="water", unit="L")
    db_session.add(m)
    db_session.commit()

    now = datetime.now(timezone.utc)
    t1 = now - timedelta(days=2)
    t2 = now - timedelta(days=1)

    db_session.add_all([
        ConsumptionReading(meter_id=m.id, timestamp=t1, value=300.0),
        ConsumptionReading(meter_id=m.id, timestamp=t2, value=450.0),
    ])
    db_session.commit()

    response = client.get("/api/resources/history?resource=water&range=7d")
    assert response.status_code == 200
    data = response.json()
    assert data["resource"] == "water"
    assert data["unit"] == "L"
    assert data["range"] == "7d"
    assert len(data["data"]) == 2
    assert data["data"][0]["value"] == 300.0
    assert data["data"][1]["value"] == 450.0


def test_invalid_resource_and_range(client):
    """Test 6: Validates parameters and returns HTTP 400 for invalid inputs."""
    # Invalid resource
    resp1 = client.get("/api/resources/history?resource=solar&range=7d")
    assert resp1.status_code == 400
    assert "Invalid resource" in resp1.json()["detail"]

    # Invalid range
    resp2 = client.get("/api/resources/history?resource=electricity&range=90d")
    assert resp2.status_code == 400
    assert "Invalid range" in resp2.json()["detail"]


def test_invalid_ml_and_insights_parameters(client):
    """Test 7: Validates parameter bounds across ML and Insights endpoints."""
    # Invalid ML anomaly resource
    r1 = client.get("/api/ml/anomalies?resource=geothermal&range=7d")
    assert r1.status_code == 400
    assert "Invalid resource" in r1.json()["detail"]

    # Invalid ML anomaly range
    r2 = client.get("/api/ml/anomalies?resource=water&range=14d")
    assert r2.status_code == 400
    assert "Invalid range" in r2.json()["detail"]

    # Invalid ML forecast horizon (bounds check: ge=1, le=168)
    r3 = client.get("/api/ml/forecast?resource=electricity&horizon=0")
    assert r3.status_code == 422  # Pydantic Query validation

    r4 = client.get("/api/ml/forecast?resource=electricity&horizon=200")
    assert r4.status_code == 422

    # Invalid ML evaluation resource
    r5 = client.get("/api/ml/evaluation?resource=wind")
    assert r5.status_code == 400

    # Invalid Insights resource
    r6 = client.get("/api/insights?resource=biomass&range=7d")
    assert r6.status_code == 400

    # Invalid Insights range
    r7 = client.get("/api/insights?resource=water&range=60d")
    assert r7.status_code == 400


def test_intervention_404_and_invalid_inputs(client):
    """Test 8: Validates graceful 404 handling for nonexistent intervention and insight IDs."""
    # Nonexistent intervention ID
    r1 = client.get("/api/interventions/999999")
    assert r1.status_code == 404
    assert "not found" in r1.json()["detail"].lower()

    r2 = client.post("/api/interventions/999999/simulate", json={"simulated_reduction_factor": 0.85})
    assert r2.status_code == 404
    assert "not found" in r2.json()["detail"].lower()

    r3 = client.post("/api/interventions/999999/complete")
    assert r3.status_code == 404
    assert "not found" in r3.json()["detail"].lower()

    # Nonexistent insight ID on create
    r4 = client.post("/api/interventions", json={"insight_id": 999999, "action": "Fix pipe"})
    assert r4.status_code == 404
    assert "not found" in r4.json()["detail"].lower()


def test_ml_forecasting_determinism(client, db_session):
    """Test 9: Verifies forecasting produces deterministic outputs across repeated calls."""
    b = Building(name="Determinism Hall", type="Academic", sqft=50000)
    db_session.add(b)
    db_session.commit()

    m = ResourceMeter(building_id=b.id, resource_type="electricity", unit="kWh")
    db_session.add(m)
    db_session.commit()

    now = datetime.now(timezone.utc)
    readings = [
        ConsumptionReading(meter_id=m.id, timestamp=now - timedelta(hours=i), value=100.0 + (i % 20))
        for i in range(50)
    ]
    db_session.add_all(readings)
    db_session.commit()

    # Call forecast twice
    res1 = client.get("/api/ml/forecast?resource=electricity&horizon=12")
    res2 = client.get("/api/ml/forecast?resource=electricity&horizon=12")

    assert res1.status_code == 200
    assert res2.status_code == 200

    preds1 = res1.json()["predictions"]
    preds2 = res2.json()["predictions"]

    assert len(preds1) == 12
    assert len(preds2) == 12
    for p1, p2 in zip(preds1, preds2):
        assert p1["predicted_value"] == p2["predicted_value"]

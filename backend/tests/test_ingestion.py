"""Comprehensive test suite for Milestone 5B: Data Ingestion MVP.

Verifies:
1. Valid CSV upload
2. Missing required column
3. Invalid timestamp
4. Unknown building
5. Invalid resource type
6. Non-numeric value
7. Negative value
8. Empty CSV
9. Duplicate row in CSV
10. Multiple valid rows across buildings
11. Database insertion verification
12. Import response counts accuracy
13. No duplicate database records on re-upload
14. Database remains unchanged after failed validation
15. Template download endpoint
"""
import io
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.campus import Building, ResourceMeter, ConsumptionReading

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory database for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Pre-seed standard buildings and meters
    b1 = Building(name="Central Library", type="Academic", sqft=110000)
    b2 = Building(name="Evergreen Residence Hall", type="Residential", sqft=95000)
    b3 = Building(name="Campus Student Center", type="Student Life", sqft=85000)
    session.add_all([b1, b2, b3])
    session.flush()

    m1_elec = ResourceMeter(building_id=b1.id, resource_type="electricity", unit="kWh")
    m1_water = ResourceMeter(building_id=b1.id, resource_type="water", unit="L")
    m2_water = ResourceMeter(building_id=b2.id, resource_type="water", unit="L")
    m3_waste = ResourceMeter(building_id=b3.id, resource_type="waste", unit="kg")
    session.add_all([m1_elec, m1_water, m2_water, m3_waste])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Test client overriding get_db to connect to the in-memory test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_csv_file(content: str, filename: str = "test.csv"):
    """Helper to construct a multipart upload tuple."""
    return {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")}


# 1. Valid CSV upload
def test_valid_csv_upload(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,82.4\n"
        "2026-09-01 11:00:00,Central Library,electricity,85.1\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert data["imported_rows"] == 2
    assert data["invalid_rows"] == 0
    assert data["duplicate_rows"] == 0
    assert len(data["errors"]) == 0


# 2. Missing required column
def test_missing_required_column(client):
    csv_data = (
        "timestamp,building,value\n"  # missing resource_type
        "2026-09-01 10:00:00,Central Library,82.4\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 400
    assert "Missing required CSV column" in res.json()["detail"]


# 3. Invalid timestamp
def test_invalid_timestamp(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "not-a-valid-timestamp,Central Library,electricity,82.4\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 1
    assert data["invalid_rows"] == 1
    assert data["imported_rows"] == 0
    assert any("Invalid timestamp" in err for err in data["errors"])


# 4. Unknown building
def test_unknown_building(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,NonExistent Building XYZ,electricity,82.4\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["invalid_rows"] == 1
    assert data["imported_rows"] == 0
    assert any("Unknown building" in err for err in data["errors"])


# 5. Invalid resource type
def test_invalid_resource_type(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,diesel_fuel,82.4\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["invalid_rows"] == 1
    assert data["imported_rows"] == 0
    assert any("Invalid resource_type" in err for err in data["errors"])


# 6. Non-numeric value
def test_non_numeric_value(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,high_power\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["invalid_rows"] == 1
    assert data["imported_rows"] == 0
    assert any("Value must be numeric" in err for err in data["errors"])


# 7. Negative value
def test_negative_value(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,-15.5\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["invalid_rows"] == 1
    assert data["imported_rows"] == 0
    assert any("Value cannot be negative" in err for err in data["errors"])


# 8. Empty CSV
def test_empty_csv(client):
    csv_data = ""
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# 9. Duplicate row in CSV (in-batch duplicate)
def test_duplicate_row_in_csv(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,82.4\n"
        "2026-09-01 10:00:00,Central Library,electricity,82.4\n"  # Exact duplicate timestamp
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 1
    assert data["imported_rows"] == 1
    assert data["duplicate_rows"] == 1
    assert len(data["warnings"]) >= 1
    assert any("Duplicate" in w for w in data["warnings"])


# 10. Multiple valid rows across buildings and resources
def test_multiple_valid_rows_across_buildings(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,82.4\n"
        "2026-09-01 10:00:00,Evergreen Residence Hall,water,420.0\n"
        "2026-09-01 00:00:00,Campus Student Center,waste,320.0\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 3
    assert data["valid_rows"] == 3
    assert data["imported_rows"] == 3
    assert data["invalid_rows"] == 0


# 11. Database insertion verification
def test_database_insertion_verified(client, db_session):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 12:00:00,Central Library,electricity,95.5\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200

    # Query DB directly to verify persistence
    reading = db_session.query(ConsumptionReading).filter(
        ConsumptionReading.value == 95.5
    ).first()
    assert reading is not None
    assert reading.timestamp == datetime(2026, 9, 1, 12, 0, 0)
    assert reading.is_anomaly is False


# 12. Import response counts accuracy (mixed valid, invalid, duplicate)
def test_import_response_counts_accuracy(client):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 10:00:00,Central Library,electricity,82.4\n"  # Valid 1
        "2026-09-01 11:00:00,Central Library,electricity,85.1\n"  # Valid 2
        "2026-09-01 11:00:00,Central Library,electricity,85.1\n"  # Duplicate of valid 2
        "2026-09-01 12:00:00,Unknown Complex,electricity,90.0\n"  # Invalid (bad building)
        "2026-09-01 13:00:00,Central Library,electricity,-10.0\n" # Invalid (negative)
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 5
    assert data["valid_rows"] == 2
    assert data["imported_rows"] == 2
    assert data["duplicate_rows"] == 1
    assert data["invalid_rows"] == 2
    assert len(data["errors"]) == 2
    assert len(data["warnings"]) == 1


# 13. No duplicate database records on re-upload
def test_no_duplicate_db_records_on_reupload(client, db_session):
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "2026-09-01 14:00:00,Central Library,electricity,100.0\n"
    )
    # First upload
    res1 = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res1.status_code == 200
    assert res1.json()["imported_rows"] == 1

    # Second upload with identical record
    res2 = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["imported_rows"] == 0
    assert data2["duplicate_rows"] == 1

    # Ensure exactly 1 row exists in DB
    count = db_session.query(ConsumptionReading).filter(
        ConsumptionReading.value == 100.0
    ).count()
    assert count == 1


# 14. Database remains unchanged after failed validation
def test_database_unchanged_after_failed_validation(client, db_session):
    # Record initial reading count
    initial_count = db_session.query(ConsumptionReading).count()

    # Upload completely invalid CSV
    csv_data = (
        "timestamp,building,resource_type,value\n"
        "bad-date,Unknown,bad-res,-999\n"
    )
    res = client.post("/api/ingestion/upload", files=make_csv_file(csv_data))
    assert res.status_code == 200
    assert res.json()["imported_rows"] == 0
    assert res.json()["invalid_rows"] == 1

    # Count must be exactly the same
    final_count = db_session.query(ConsumptionReading).count()
    assert final_count == initial_count


# 15. Template download endpoint
def test_download_csv_template(client):
    res = client.get("/api/ingestion/template")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=campus_resource_template.csv" in res.headers.get("content-disposition", "")
    content = res.text
    assert "timestamp,building,resource_type,value" in content
    assert "Central Library" in content
    assert "electricity" in content

"""Seed Data Generator for Campus Resource Autopilot.

Populates the SQLite database with 30 days of realistic, reproducible hourly and
daily telemetry across multiple campus buildings, meters, and resources. Includes
deliberate anomalies for demonstration purposes.
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta, timezone

# Ensure backend root is in sys.path when running script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.models.campus import Building, ResourceMeter, ConsumptionReading, Insight, Intervention

# Ensure deterministic output
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BUILDINGS_SPEC = [
    {
        "name": "Science & Engineering Complex",
        "type": "Academic/Lab",
        "sqft": 125000,
        "base_elec_kwh": 180.0,
        "base_water_l": 450.0,
        "base_waste_kg": 280.0,
    },
    {
        "name": "Campus Student Center",
        "type": "Student Life",
        "sqft": 85000,
        "base_elec_kwh": 95.0,
        "base_water_l": 320.0,
        "base_waste_kg": 340.0,
    },
    {
        "name": "Evergreen Residence Hall",
        "type": "Residential",
        "sqft": 95000,
        "base_elec_kwh": 80.0,
        "base_water_l": 620.0,
        "base_waste_kg": 210.0,
    },
    {
        "name": "Central Library",
        "type": "Academic",
        "sqft": 110000,
        "base_elec_kwh": 110.0,
        "base_water_l": 210.0,
        "base_waste_kg": 140.0,
    },
    {
        "name": "Summit Dining Commons",
        "type": "Dining",
        "sqft": 42000,
        "base_elec_kwh": 130.0,
        "base_water_l": 750.0,
        "base_waste_kg": 420.0,
    },
]


def generate_diurnal_factor(hour: int, b_type: str, is_weekend: bool) -> float:
    """Calculates a realistic hourly occupancy consumption multiplier."""
    if b_type == "Residential":
        # Peaks in morning (7-9am) and evening (6-11pm), sustained on weekends
        if 7 <= hour <= 9:
            factor = 1.4
        elif 18 <= hour <= 23:
            factor = 1.6
        elif 1 <= hour <= 5:
            factor = 0.35
        else:
            factor = 0.8
        if is_weekend:
            factor *= 1.2
        return factor

    elif b_type == "Dining":
        # Peaks around breakfast, lunch, and dinner
        if 7 <= hour <= 9:
            factor = 1.6
        elif 11 <= hour <= 14:
            factor = 1.9
        elif 17 <= hour <= 20:
            factor = 1.8
        elif 0 <= hour <= 5:
            factor = 0.15
        else:
            factor = 0.6
        if is_weekend:
            factor *= 0.85
        return factor

    else:
        # Academic & Student Centers
        if is_weekend:
            # Low occupancy on weekends
            if 10 <= hour <= 17:
                return 0.4
            return 0.2
        else:
            # Active 8am-7pm weekdays
            if 8 <= hour <= 18:
                return 1.2 + 0.3 * math.sin((hour - 8) / 10.0 * math.pi)
            elif 19 <= hour <= 22:
                return 0.6
            else:
                return 0.25


def seed_database(clear_existing: bool = True):
    """Generates 30 days of realistic time-series data with deliberate anomalies."""
    print("[seed] Ensuring tables are created...")
    init_db()

    db = SessionLocal()
    try:
        if clear_existing:
            print("[seed] Clearing existing data for fresh seed...")
            db.query(Intervention).delete()
            db.query(Insight).delete()
            db.query(ConsumptionReading).delete()
            db.query(ResourceMeter).delete()
            db.query(Building).delete()
            db.commit()

        print("[seed] Creating campus buildings and meters...")
        building_records = []
        meters = []

        for b_spec in BUILDINGS_SPEC:
            building = Building(
                name=b_spec["name"],
                type=b_spec["type"],
                sqft=b_spec["sqft"],
            )
            db.add(building)
            db.flush()
            building_records.append((building, b_spec))

            # 3 meters per building: Electricity, Water, Waste
            m_elec = ResourceMeter(building_id=building.id, resource_type="electricity", unit="kWh")
            m_water = ResourceMeter(building_id=building.id, resource_type="water", unit="L")
            m_waste = ResourceMeter(building_id=building.id, resource_type="waste", unit="kg")
            db.add_all([m_elec, m_water, m_waste])
            db.flush()

            meters.append({
                "building": building,
                "spec": b_spec,
                "elec_meter": m_elec,
                "water_meter": m_water,
                "waste_meter": m_waste,
            })

        db.commit()

        now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start_utc = now_utc - timedelta(days=30)
        total_hours = 30 * 24

        readings_batch = []
        anomaly_count = 0
        print(f"[seed] Generating 30 days ({total_hours} hours) of telemetry readings...")

        # 1. Generate Hourly Readings for Electricity and Water
        for hour_step in range(total_hours):
            current_time = start_utc + timedelta(hours=hour_step)
            hour_of_day = current_time.hour
            is_weekend = current_time.weekday() >= 5
            day_number = hour_step // 24

            for item in meters:
                b_spec = item["spec"]
                b_name = b_spec["name"]
                b_type = b_spec["type"]
                factor = generate_diurnal_factor(hour_of_day, b_type, is_weekend)

                # Add natural minor random noise (+/- 5%)
                noise = random.uniform(0.95, 1.05)

                # Base electricity calculation
                elec_val = round(b_spec["base_elec_kwh"] * factor * noise, 2)
                elec_anomaly = False

                # Base water calculation
                water_val = round(b_spec["base_water_l"] * factor * noise, 2)
                water_anomaly = False

                # --- Deliberate Anomaly 1: Water Pipe Leak in Evergreen Residence Hall (Days 22 to 24) ---
                if b_name == "Evergreen Residence Hall" and (22 <= day_number <= 24):
                    # Constant +420 L/hr leak regardless of hour
                    water_val = round(water_val + 420.0 + random.uniform(20.0, 50.0), 2)
                    water_anomaly = True
                    anomaly_count += 1

                # --- Deliberate Anomaly 2: Weekend HVAC Power Surge in Central Library (Day 15) ---
                if b_name == "Central Library" and day_number == 15 and is_weekend:
                    # Equipment failure causes extreme power draw (3.2x normal weekend)
                    elec_val = round(elec_val * 3.2 + random.uniform(30.0, 60.0), 2)
                    elec_anomaly = True
                    anomaly_count += 1

                readings_batch.append(
                    ConsumptionReading(
                        meter_id=item["elec_meter"].id,
                        timestamp=current_time,
                        value=elec_val,
                        is_anomaly=elec_anomaly,
                    )
                )

                readings_batch.append(
                    ConsumptionReading(
                        meter_id=item["water_meter"].id,
                        timestamp=current_time,
                        value=water_val,
                        is_anomaly=water_anomaly,
                    )
                )

            # Commit in batches of 1,000 for performance
            if len(readings_batch) >= 1000:
                db.bulk_save_objects(readings_batch)
                db.commit()
                readings_batch = []

        # 2. Generate Daily Waste Readings (30 days, logged at 23:00 UTC)
        for day_step in range(30):
            day_time = (start_utc + timedelta(days=day_step)).replace(hour=23, minute=0, second=0)
            is_weekend = day_time.weekday() >= 5

            for item in meters:
                b_spec = item["spec"]
                b_name = b_spec["name"]
                b_type = b_spec["type"]

                waste_factor = 0.5 if (is_weekend and b_type != "Residential") else 1.0
                waste_noise = random.uniform(0.92, 1.08)
                waste_val = round(b_spec["base_waste_kg"] * waste_factor * waste_noise, 2)
                waste_anomaly = False

                # --- Deliberate Anomaly 3: Post-Festival Waste Surge at Student Center (Day 28) ---
                if b_name == "Campus Student Center" and day_step == 28:
                    waste_val = round(waste_val * 4.5, 2)  # Huge spike post event
                    waste_anomaly = True
                    anomaly_count += 1

                readings_batch.append(
                    ConsumptionReading(
                        meter_id=item["waste_meter"].id,
                        timestamp=day_time,
                        value=waste_val,
                        is_anomaly=waste_anomaly,
                    )
                )

        if readings_batch:
            db.bulk_save_objects(readings_batch)
            db.commit()

        total_readings = db.query(ConsumptionReading).count()
        print(f"[seed] Success! Created {len(building_records)} buildings, {len(meters)*3} meters.")
        print(f"[seed] Inserted {total_readings} consumption readings ({anomaly_count} deliberate anomaly points).")

    except Exception as e:
        db.rollback()
        print(f"[seed] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(clear_existing=True)

"""Standalone verification script for Milestone 4B: Impact & Savings Measurement."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from fastapi.testclient import TestClient
from app.main import app

def verify_impact():
    client = TestClient(app)

    print("=" * 60)
    print("CAMPUS RESOURCE AUTOPILOT - MILESTONE 4B VERIFICATION")
    print("=" * 60)

    # 1. Fetch insights
    ins_elec = client.get("/api/insights?resource=electricity&range=7d").json()["insights"][0]
    ins_water = client.get("/api/insights?resource=water&range=7d").json()["insights"][0]
    ins_waste = client.get("/api/insights?resource=waste&range=30d").json()["insights"][0]

    print(f"\n[INSIGHT - Electricity]: ID={ins_elec['id']} | {ins_elec['title']}")
    print(f"[INSIGHT - Water]:       ID={ins_water['id']} | {ins_water['title']}")
    print(f"[INSIGHT - Waste]:       ID={ins_waste['id']} | {ins_waste['title']}")

    # 2. Create interventions
    itv_elec = client.post("/api/interventions", json={"insight_id": int(ins_elec["id"])}).json()
    itv_water = client.post("/api/interventions", json={"insight_id": int(ins_water["id"])}).json()
    itv_waste = client.post("/api/interventions", json={"insight_id": int(ins_waste["id"])}).json()

    print(f"\n[CREATED INTERVENTIONS]")
    print(f"Electricity ITV #{itv_elec['id']} Status: {itv_elec['status']}")
    print(f"Water ITV #{itv_water['id']} Status: {itv_water['status']}")
    print(f"Waste ITV #{itv_waste['id']} Status: {itv_waste['status']}")

    # 3. Simulate interventions
    sim_elec = client.post(f"/api/interventions/{itv_elec['id']}/simulate", json={"simulated_reduction_factor": 0.85}).json()
    sim_water = client.post(f"/api/interventions/{itv_water['id']}/simulate", json={"simulated_reduction_factor": 0.85}).json()
    sim_waste = client.post(f"/api/interventions/{itv_waste['id']}/simulate", json={"simulated_reduction_factor": 0.85}).json()

    print(f"\n[SIMULATED DEMO IMPACT]")
    print(f"Electricity: Before={sim_elec['before_value']} {sim_elec['unit']} -> After={sim_elec['after_value']} {sim_elec['unit']} | Saved: {sim_elec['estimated_savings']} {sim_elec['unit']} (-{sim_elec['savings_percentage']}%)")
    print(f"Water:       Before={sim_water['before_value']} {sim_water['unit']} -> After={sim_water['after_value']} {sim_water['unit']} | Saved: {sim_water['estimated_savings']} {sim_water['unit']} (-{sim_water['savings_percentage']}%)")
    print(f"Waste:       Before={sim_waste['before_value']} {sim_waste['unit']} -> After={sim_waste['after_value']} {sim_waste['unit']} | Saved: {sim_waste['estimated_savings']} {sim_waste['unit']} (-{sim_waste['savings_percentage']}%)")

    # 4. Impact Summary
    summary = client.get("/api/impact/summary").json()
    print("\n[AGGREGATE IMPACT SUMMARY]")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    verify_impact()

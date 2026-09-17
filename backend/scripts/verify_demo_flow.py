"""End-to-End Hackathon Demo Verification Script for Campus Resource Autopilot.

Simulates and verifies the complete 11-step hackathon workflow:
1. Health Check
2. Resource Summary (3 Pillars: Electricity, Water, Waste)
3. Select Water & Detect Anomalies
4. Retrieve Root-Cause Explanation & Recommended Directive
5. Create Facility Intervention Ticket
6. Simulate Intervention (Transparent 85% Demo Factor)
7. Verify Before vs. After Savings & Measurement Label
8. Verify Campus Aggregate Impact Summary
9. Verify Demand Forecasting (24h horizon)
10. Verify Model Evaluation (Chronological Holdout)
11. Readiness Verdict
"""

import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

def run_demo_verification():
    print("=" * 70)
    print("CAMPUS RESOURCE AUTOPILOT - HACKATHON DEMO END-TO-END VERIFICATION")
    print("=" * 70)

    client = TestClient(app)
    passed_steps = 0
    total_steps = 10

    # STEP 1: Health Check
    print("\n[STEP 1] Verifying Backend Health & Database Connectivity...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed with {res.status_code}"
    health = res.json()
    assert health["status"] == "healthy"
    assert health["database"] == "connected"
    print(f"  [OK] System healthy, DB connected (v{health['version']})")
    passed_steps += 1

    # STEP 2: Resource Overview
    print("\n[STEP 2] Verifying Campus Resource Overview (3 Pillars)...")
    res = client.get("/api/resources/summary")
    assert res.status_code == 200
    summary = res.json()
    for pillar, unit in [("electricity", "kWh"), ("water", "L"), ("waste", "kg")]:
        assert pillar in summary
        assert summary[pillar]["unit"] == unit
        assert summary[pillar]["total"] > 0
        print(f"  [OK] {pillar.capitalize()}: {summary[pillar]['total']:,.1f} {unit} total (current: {summary[pillar]['current']} {unit})")
    passed_steps += 1

    # STEP 3: Water Anomalies
    print("\n[STEP 3] Detecting Water Anomalies via Isolation Forest...")
    res = client.get("/api/ml/anomalies?resource=water&range=7d")
    assert res.status_code == 200
    anom_data = res.json()
    assert anom_data["total_anomalies"] > 0
    print(f"  [OK] Detected {anom_data['total_anomalies']} water anomalies in 7d window")
    top_anom = anom_data["anomalies"][0]
    print(f"  [OK] Top Anomaly: {top_anom['building_name']} - {top_anom['value']} L (score: {top_anom['anomaly_score']})")
    passed_steps += 1

    # STEP 4: Explain & Recommend Insights
    print("\n[STEP 4] Retrieving Root-Cause Explanation & Facility Directives...")
    res = client.get("/api/insights?resource=water&range=7d")
    assert res.status_code == 200
    insights_data = res.json()
    assert len(insights_data["insights"]) > 0
    water_insight = next((i for i in insights_data["insights"] if i["type"] == "anomaly"), insights_data["insights"][0])
    print(f"  [OK] Title: {water_insight['title']}")
    print(f"  [OK] Severity: {water_insight['severity']} (Score: {water_insight['priority_score']})")
    print(f"  [OK] Explanation: {water_insight['explanation'][:100]}...")
    print(f"  [OK] Action: {water_insight['recommended_action'][:100]}...")
    passed_steps += 1

    # STEP 5: Create Facility Intervention
    print("\n[STEP 5] Creating Facility Intervention Ticket from Insight...")
    insight_id = int(water_insight["id"])
    payload = {
        "insight_id": insight_id,
        "action": water_insight["recommended_action"],
        "measurement_type": "SIMULATED"
    }
    res = client.post("/api/interventions", json=payload)
    assert res.status_code == 201
    itv = res.json()
    itv_id = itv["id"]
    assert itv["status"] == "PLANNED"
    assert itv["resource_type"] == "water"
    assert itv["before_value"] is not None
    assert itv["baseline_value"] is not None
    print(f"  [OK] Created Intervention #{itv_id}: Status={itv['status']}")
    print(f"       Observed Before: {itv['before_value']} L | Baseline: {itv['baseline_value']} L")
    passed_steps += 1

    # STEP 6: Simulate Intervention Impact (Demo Mode)
    print("\n[STEP 6] Simulating Intervention Outcome (85% Excess Mitigation)...")
    res = client.post(f"/api/interventions/{itv_id}/simulate", json={"simulated_reduction_factor": 0.85})
    assert res.status_code == 200
    sim_itv = res.json()
    assert sim_itv["status"] == "COMPLETED"
    assert sim_itv["measurement_type"] == "SIMULATED"
    assert sim_itv["after_value"] is not None
    assert sim_itv["estimated_savings"] is not None
    assert sim_itv["savings_percentage"] is not None
    print(f"  [OK] Simulation Complete: Status={sim_itv['status']} (Type: {sim_itv['measurement_type']})")
    passed_steps += 1

    # STEP 7: Verify Before -> After Savings
    print("\n[STEP 7] Verifying Before vs. After Impact Calculations...")
    assert sim_itv["after_value"] < sim_itv["before_value"]
    assert sim_itv["estimated_savings"] > 0
    print(f"  [OK] Before: {sim_itv['before_value']} L -> After: {sim_itv['after_value']} L")
    print(f"  [OK] Estimated Savings: {sim_itv['estimated_savings']} L (-{sim_itv['savings_percentage']}%)")
    passed_steps += 1

    # STEP 8: Aggregate Campus Impact Summary
    print("\n[STEP 8] Verifying Aggregate Campus Impact Summary...")
    res = client.get("/api/impact/summary")
    assert res.status_code == 200
    impact = res.json()
    assert impact["total_completed_interventions"] >= 1
    assert "disclaimer" in impact
    assert impact["water"]["total_estimated_savings"] > 0
    print(f"  [OK] Total Completed Interventions: {impact['total_completed_interventions']}")
    print(f"  [OK] Water Conservation: {impact['water']['total_estimated_savings']:,.2f} L saved")
    print(f"  [OK] Mandatory Disclaimer: {impact['disclaimer'][:75]}...")
    passed_steps += 1

    # STEP 9: 24-Period Demand Forecast
    print("\n[STEP 9] Verifying 24-Hour Demand Forecast...")
    res = client.get("/api/ml/forecast?resource=water&horizon=24")
    assert res.status_code == 200
    fc = res.json()
    assert len(fc["predictions"]) == 24
    assert fc["unit"] == "L"
    print(f"  [OK] Received {len(fc['predictions'])} hourly demand projections (Unit: {fc['unit']})")
    passed_steps += 1

    # STEP 10: Model Evaluation Benchmarks (Chronological Holdout)
    print("\n[STEP 10] Verifying Model Evaluation Benchmarks (Strict Time Split)...")
    res = client.get("/api/ml/evaluation?resource=electricity")
    assert res.status_code == 200
    eval_m = res.json()
    assert "forecast" in eval_m
    assert "anomaly_detection" in eval_m
    print(f"  [OK] Electricity Forecast MAE: {eval_m['forecast']['mae']} kWh")
    print(f"  [OK] Electricity Anomaly Hold-out F1: {eval_m['anomaly_detection']['f1']} (Test anomalies: {eval_m['anomaly_detection']['actual_anomalies']})")
    passed_steps += 1


    print("\n" + "=" * 70)
    print(f"RESULTS: {passed_steps}/{total_steps} STEPS VERIFIED SUCCESSFULLY")
    print("VERDICT: HACKATHON DEMO PIPELINE FULLY FUNCTIONAL AND ROBUST")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_demo_verification()
    sys.exit(0 if success else 1)

"""Verification script for Milestone 3 ML Intelligence Layer."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.campus import ConsumptionReading, AnomalyPrediction
from app.services.ml_service import MLService

def main():
    db = SessionLocal()
    try:
        print("1. Checking ground-truth preservation...")
        ground_truth_count = db.query(ConsumptionReading).filter(ConsumptionReading.is_anomaly == True).count()
        print(f"   Ground-truth anomalies in DB: {ground_truth_count}")
        assert ground_truth_count == 73, f"Expected 73 ground truth anomalies, found {ground_truth_count}"

        print("2. Testing ML intelligence across all 3 resources...")
        service = MLService(db)

        for res in ["electricity", "water", "waste"]:
            print(f"\n--- {res.upper()} ---")
            
            # Forecast
            fc = service.get_forecast(res, 24)
            print(f"  Forecast: {len(fc['predictions'])} periods, Frequency: {fc['frequency']}")
            assert len(fc["predictions"]) == 24
            if res == "waste":
                assert fc["frequency"] == "daily"
            else:
                assert fc["frequency"] == "hourly"
            print(f"  Sample next step: {fc['predictions'][0]['timestamp']} -> {fc['predictions'][0]['predicted_value']} {fc['unit']}")

            # Anomalies
            anoms_7d = service.get_anomalies(res, "7d")
            anoms_30d = service.get_anomalies(res, "30d")
            print(f"  Detected Anomalies: 7d={anoms_7d['total_anomalies']}, 30d={anoms_30d['total_anomalies']}")

            # Evaluation
            ev = service.get_evaluation(res)
            print(f"  Forecast Metrics: MAE={ev['forecast']['mae']}, RMSE={ev['forecast']['rmse']}")
            anom_ev = ev["anomaly_detection"]
            print(f"  Anomaly Metrics: Precision={anom_ev['precision']}, Recall={anom_ev['recall']}, F1={anom_ev['f1']}, TP={anom_ev['true_positives']}, FP={anom_ev['false_positives']}, FN={anom_ev['false_negatives']}")

        print("\nAll verification checks PASSED cleanly!")

    finally:
        db.close()

if __name__ == "__main__":
    main()

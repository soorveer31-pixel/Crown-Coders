"""Insights Service Module for Campus Resource Autopilot.

Integrates machine learning anomaly detection and short-term demand forecasting
with the Explanation and Recommendation Engines to generate structured, actionable insights.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.services.ml_service import MLService
from app.services.recommendation_service import RecommendationService
from app.ml.features import extract_features
from app.ml.predictor import RESOURCE_UNITS
from app.models.campus import Insight


class InsightsService:
    """Orchestrates end-to-end telemetry explanation and recommendation pipelines."""

    SUPPORTED_RESOURCES = ["electricity", "water", "waste"]
    SUPPORTED_RANGES = ["7d", "30d"]

    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLService(db)

    def get_insights(
        self,
        resource: Optional[str] = None,
        range_str: str = "7d",
        persist: bool = False,
    ) -> Dict[str, Any]:
        """Generates structured detected issues (anomalies) and upcoming risks (forecast spikes).

        Args:
            resource: Optional filter for 'electricity', 'water', or 'waste'.
            range_str: Time window filter ('7d' or '30d').
            persist: If True, saves generated insights to the SQLite database.

        Returns:
            Dictionary conforming to InsightsResponse schema.
        """
        range_key = range_str.lower().strip()
        if range_key not in self.SUPPORTED_RANGES:
            raise ValueError(f"Invalid range '{range_str}'. Supported: {', '.join(self.SUPPORTED_RANGES)}")

        target_resources = []
        if resource:
            res_key = resource.lower().strip()
            if res_key not in self.SUPPORTED_RESOURCES:
                raise ValueError(f"Invalid resource '{resource}'. Supported: {', '.join(self.SUPPORTED_RESOURCES)}")
            target_resources = [res_key]
        else:
            target_resources = self.SUPPORTED_RESOURCES

        detected_issues: List[Dict[str, Any]] = []
        upcoming_risks: List[Dict[str, Any]] = []

        days = 7 if range_key == "7d" else 30

        for res_type in target_resources:
            unit = RESOURCE_UNITS.get(res_type, "")
            df = self.ml_service._load_telemetry_df(res_type)
            if df.empty:
                continue

            # 1. Feature extraction to obtain exact backward rolling baselines
            features_df = extract_features(df, resource_type=res_type, group_col="meter_id")

            # 2. Isolation Forest anomaly scoring
            pred_df = self.ml_service.predictor.detect_anomalies(res_type, df, group_col="meter_id")
            features_df["predicted_anomaly"] = pred_df["predicted_anomaly"].values
            features_df["anomaly_score"] = pred_df["anomaly_score"].values

            # 3. Filter by time window
            max_ts = features_df["timestamp"].max()
            cutoff = max_ts - timedelta(days=days)
            window_df = features_df[features_df["timestamp"] >= cutoff]

            # 4. Process Detected Anomalies
            anom_rows = window_df[window_df["predicted_anomaly"] == True]
            for _, row in anom_rows.iterrows():
                ts = row["timestamp"]
                dt = ts if isinstance(ts, datetime) else pd.to_datetime(ts).to_pydatetime()

                rec = RecommendationService.generate_anomaly_recommendation(
                    resource_type=res_type,
                    observed_value=float(row["value"]),
                    expected_value=float(row["rolling_mean"]),
                    timestamp=dt,
                    anomaly_score=float(row["anomaly_score"]),
                    building_name=str(row.get("building_name", "Campus Facility")),
                    unit=unit,
                )
                detected_issues.append(rec)

            # 5. Process Forecast-based Proactive Risks
            try:
                forecast_res = self.ml_service.get_forecast(res_type, horizon=24)
                predictions = forecast_res.get("predictions", [])

                # Compute campus baseline for the resource
                agg_df = df.groupby("timestamp", as_index=False)["value"].sum()
                recent_baseline = float(agg_df["value"].mean()) if not agg_df.empty else 1.0

                for pred_pt in predictions:
                    risk = RecommendationService.generate_forecast_risk_insight(
                        resource_type=res_type,
                        predicted_point=pred_pt,
                        historical_baseline=recent_baseline,
                        threshold_multiplier=1.20,
                    )
                    if risk:
                        upcoming_risks.append(risk)
            except Exception:
                pass  # Do not block anomaly insights if forecast is unavailable

        # Sort detected issues by priority score descending
        detected_issues.sort(key=lambda x: x["priority_score"], reverse=True)

        # Sort upcoming risks by timestamp ascending
        upcoming_risks.sort(key=lambda x: x["timestamp"])

        # Limit to top insights to avoid overwhelming users
        selected_issues = detected_issues[:20]
        selected_risks = upcoming_risks[:10]

        all_insights = selected_issues + selected_risks

        # Persist/sync insights in database so interventions can reference authentic IDs
        for idx, item in enumerate(all_insights, start=1):
            try:
                dt = pd.to_datetime(item["timestamp"]).to_pydatetime()
                existing = (
                    self.db.query(Insight)
                    .filter(
                        Insight.resource_type == item["resource"],
                        Insight.building_name == item["building"],
                        Insight.timestamp == dt,
                        Insight.insight_type == item["type"],
                    )
                    .first()
                )
                if not existing:
                    existing = Insight(
                        resource_type=item["resource"],
                        building_name=item["building"],
                        timestamp=dt,
                        insight_type=item["type"],
                        severity=item["severity"],
                        priority_score=item["priority_score"],
                        title=item["title"],
                        explanation=item["explanation"],
                        recommendation=item["recommendation"],
                        recommended_action=item["recommended_action"],
                        observed_value=float(item.get("observed_value", 0.0)),
                        expected_value=float(item.get("expected_value", 0.0)),
                    )
                    self.db.add(existing)
                    self.db.commit()
                    self.db.refresh(existing)

                item["id"] = str(existing.id)
            except Exception:
                self.db.rollback()
                item["id"] = f"ins-{item['resource']}-{idx}"

        return {
            "resource": resource or "all",
            "range": range_key,
            "total_insights": len(all_insights),
            "detected_issues_count": len(selected_issues),
            "upcoming_risks_count": len(selected_risks),
            "insights": all_insights,
        }

"""Recommendation Service Module for Campus Resource Autopilot.

Generates deterministic, actionable facility management recommendations and
forecast-based proactive risk insights using transparent priority scoring.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.explanation_service import ExplanationService

RESOURCE_WEIGHTS = {
    "water": 0.90,        # High physical damage & flood liability
    "electricity": 0.80,  # High peak demand tariff cost
    "waste": 0.70,        # Overflow and sanitary compliance
}


class RecommendationService:
    """Service producing concrete facility recommendations and priority scoring."""

    @staticmethod
    def calculate_priority(
        anomaly_score: float,
        deviation_percent: float,
        is_off_peak: bool,
        resource_type: str,
    ) -> Dict[str, Any]:
        """Calculates a transparent priority score and assigns a severity tier.

        Formula:
            Priority = 0.40 * anomaly_score
                     + 0.30 * min(1.0, max(0.0, deviation_percent) / 200.0)
                     + 0.20 * (1.0 if is_off_peak else 0.0)
                     + 0.10 * resource_weight

        Severity Tiers:
            >= 0.80 -> CRITICAL
            >= 0.65 -> HIGH
            >= 0.45 -> MEDIUM
            <  0.45 -> LOW
        """
        s_anom = min(max(float(anomaly_score), 0.0), 1.0)
        norm_dev = min(max(float(deviation_percent), 0.0) / 200.0, 1.0)
        f_offpeak = 1.0 if is_off_peak else 0.0
        f_res = RESOURCE_WEIGHTS.get(resource_type.lower().strip(), 0.75)

        raw_score = (0.40 * s_anom) + (0.30 * norm_dev) + (0.20 * f_offpeak) + (0.10 * f_res)
        priority_score = round(min(max(raw_score, 0.0), 1.0), 4)

        if priority_score >= 0.80:
            severity = "CRITICAL"
        elif priority_score >= 0.65:
            severity = "HIGH"
        elif priority_score >= 0.45:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "priority_score": priority_score,
            "severity": severity,
        }

    @classmethod
    def generate_anomaly_recommendation(
        cls,
        resource_type: str,
        observed_value: float,
        expected_value: float,
        timestamp: datetime,
        anomaly_score: float,
        building_name: Optional[str] = None,
        unit: str = "",
    ) -> Dict[str, Any]:
        """Produces a complete explained anomaly insight with concrete maintenance actions."""
        res_key = resource_type.lower().strip()
        explanation = ExplanationService.explain_anomaly(
            resource_type=res_key,
            observed_value=observed_value,
            expected_value=expected_value,
            timestamp=timestamp,
            anomaly_score=anomaly_score,
            building_name=building_name,
            unit=unit,
        )

        priority_info = cls.calculate_priority(
            anomaly_score=anomaly_score,
            deviation_percent=explanation["deviation_percent"],
            is_off_peak=explanation["is_off_peak"],
            resource_type=res_key,
        )

        b_name = building_name or "Campus Facility"
        is_off_peak = explanation["is_off_peak"]
        pct = explanation["deviation_percent"]

        # Concrete, simple-English actionable directives
        if res_key == "water":
            if is_off_peak:
                title = f"Possible Water Pipe Leak at {b_name}"
                recommendation = f"Check restrooms and water pipes in {b_name} for leaks."
                action = (
                    f"Send a plumber to {b_name} to check toilets, faucets, and isolate zone shut-off valves if a pipe leak is found."
                )
            else:
                title = f"High Water Usage Spike at {b_name}"
                recommendation = f"Check cooling towers, garden sprinklers, and kitchen faucets at {b_name}."
                action = (
                    f"Inspect cooling tower water valves, cafeteria dishwashers, and check that lawn sprinklers are not running during peak daytime hours."
                )

        elif res_key == "electricity":
            if is_off_peak:
                title = f"High Electricity Use at Night in {b_name}"
                recommendation = f"Turn off unnecessary lights, computers, and AC units in {b_name}."
                action = (
                    f"Send staff to turn off lights and equipment left running in {b_name}, and check that ventilation systems switch to night mode."
                )
            else:
                title = f"Peak Power Demand Spike at {b_name}"
                recommendation = f"Spread out heavy electrical equipment use at {b_name} to avoid high bills."
                action = (
                    f"Turn on heavy equipment one by one instead of all at once, adjust thermostat pre-cooling slightly, and avoid running big machines during peak hours."
                )

        elif res_key == "waste":
            if pct >= 100.0:
                title = f"Large Trash Build-Up After Event at {b_name}"
                recommendation = f"Bring extra garbage bins and schedule an extra trash pickup for {b_name}."
                action = (
                    f"Place extra rolling trash bins outside {b_name} and request an immediate extra pickup from the campus waste collection team."
                )
            else:
                title = f"High Waste Generation at {b_name}"
                recommendation = f"Empty recycling and trash bins more frequently at {b_name}."
                action = (
                    f"Empty trash and recycling bins twice a day instead of once, and check that cardboard boxes are flattened."
                )
        else:
            title = f"Unusual {res_key.capitalize()} Usage Spike at {b_name}"
            recommendation = f"Inspect utility meters and equipment at {b_name}."
            action = f"Check the meter and inspect connected machines to find what is causing the high reading."

        return {
            "type": "anomaly",
            "resource": res_key,
            "unit": unit,
            "building": b_name,
            "timestamp": timestamp.isoformat(),
            "severity": priority_info["severity"],
            "priority_score": priority_info["priority_score"],
            "title": title,
            "explanation": explanation["reason"],
            "observed_value": explanation["observed_value"],
            "expected_value": explanation["expected_value"],
            "deviation_percent": explanation["deviation_percent"],
            "recommendation": recommendation,
            "recommended_action": action,
        }

    @classmethod
    def generate_forecast_risk_insight(
        cls,
        resource_type: str,
        predicted_point: Dict[str, Any],
        historical_baseline: float,
        threshold_multiplier: float = 1.25,
    ) -> Optional[Dict[str, Any]]:
        """Evaluates a forecast point against historical baseline and produces a proactive risk insight if exceeded."""
        res_key = resource_type.lower().strip()
        pred_val = float(predicted_point.get("predicted_value", 0.0))
        baseline = max(float(historical_baseline), 1.0)
        unit = predicted_point.get("unit", "")
        ts_str = predicted_point.get("timestamp", "")

        if pred_val <= (baseline * threshold_multiplier):
            return None

        pct_excess = round(((pred_val - baseline) / baseline) * 100.0, 1)

        try:
            dt = datetime.fromisoformat(ts_str)
            time_label = dt.strftime("%A at %H:%M")
        except Exception:
            time_label = ts_str

        # Calculate priority based on forecast surge magnitude
        score = round(min(0.50 + (pct_excess / 200.0) * 0.40, 0.95), 4)
        severity = "CRITICAL" if score >= 0.80 else "HIGH" if score >= 0.65 else "MEDIUM"

        if res_key == "electricity":
            title = f"Peak Power Spike Expected on {time_label}"
            explanation = (
                f"The AI forecast predicts electricity use will reach {pred_val:,.1f} {unit} on {time_label}, "
                f"which is {pct_excess:+,.1f}% higher than normal ({baseline:,.1f} {unit})."
            )
            recommendation = "Pre-cool buildings before peak hours and avoid running all machines at once."
            action = (
                f"Pre-cool facilities before peak hours, and adjust thermostat setpoints during {time_label} to avoid high peak electric charges."
            )
        elif res_key == "water":
            title = f"High Water Demand Expected on {time_label}"
            explanation = (
                f"The AI forecast predicts water demand will reach {pred_val:,.1f} {unit} on {time_label}, "
                f"which is {pct_excess:+,.1f}% higher than normal ({baseline:,.1f} {unit})."
            )
            recommendation = "Fill water storage tanks early and pause automated lawn watering."
            action = (
                f"Verify campus water tanks are full before {time_label}, and pause lawn sprinklers until after the high-demand period."
            )
        else:
            title = f"High {res_key.capitalize()} Demand Expected on {time_label}"
            explanation = f"Forecast predicts {res_key} consumption will reach {pred_val:,.1f} {unit} ({pct_excess:+,.1f}% above normal of {baseline:,.1f} {unit})."
            recommendation = f"Prepare staff and resources in advance for the upcoming demand surge."
            action = f"Alert facilities team to monitor {res_key} distribution during {time_label}."

        return {
            "type": "forecast_risk",
            "resource": res_key,
            "unit": unit,
            "building": "Campus-Wide",
            "timestamp": ts_str,
            "severity": severity,
            "priority_score": score,
            "title": title,
            "explanation": explanation,
            "observed_value": round(pred_val, 2),
            "expected_value": round(baseline, 2),
            "deviation_percent": pct_excess,
            "recommendation": recommendation,
            "recommended_action": action,
        }

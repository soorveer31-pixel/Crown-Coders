"""Explanation Service Module for Campus Resource Autopilot.

Synthesizes deterministic, rule-based explanations for detected anomalies
and consumption deviations without using LLMs or generative AI.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class ExplanationService:
    """Service generating factual, human-interpretable explanations for telemetry anomalies."""

    @staticmethod
    def is_off_peak_hour(timestamp: datetime, building_name: Optional[str] = None) -> bool:
        """Determines whether a reading occurred during off-peak / unoccupied campus hours."""
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5

        # Academic / Administrative / Library / Dining: off-peak is night (20:00-07:00) or all weekend
        if building_name and any(term in building_name.lower() for term in ["academic", "library", "complex", "center", "dining"]):
            if is_weekend or (hour >= 20 or hour <= 6):
                return True

        # Residential: off-peak is deep night (01:00-06:00)
        if building_name and "residence" in building_name.lower():
            return 1 <= hour <= 5

        # General campus default: 22:00-06:00 or weekend
        return is_weekend or (hour >= 22 or hour <= 6)

    @classmethod
    def explain_anomaly(
        cls,
        resource_type: str,
        observed_value: float,
        expected_value: float,
        timestamp: datetime,
        anomaly_score: float,
        building_name: Optional[str] = None,
        unit: str = "",
    ) -> Dict[str, Any]:
        """Analyzes an anomalous reading against historical baselines and produces a structured explanation.

        Args:
            resource_type: 'electricity', 'water', or 'waste'.
            observed_value: Recorded sensor value.
            expected_value: Rolling baseline value.
            timestamp: Datetime of the observation.
            anomaly_score: Normalized Isolation Forest score (0.0 to 1.0).
            building_name: Name of facility where reading was taken.
            unit: Unit of measurement.

        Returns:
            Dictionary containing computed deviations, temporal context, and deterministic explanation text.
        """
        res_key = resource_type.lower().strip()
        expected = max(float(expected_value), 0.1)
        observed = float(observed_value)
        abs_dev = round(observed - expected, 2)
        pct_dev = round(((observed - expected) / expected) * 100.0, 1)

        hour = timestamp.hour
        day_name = timestamp.strftime("%A")
        is_off_peak = cls.is_off_peak_hour(timestamp, building_name)
        time_str = timestamp.strftime("%H:%M")
        b_name = building_name or "Campus Facility"

        # Simple, plain-English explanations that anyone can easily understand:
        if res_key == "water":
            if is_off_peak:
                reason = (
                    f"Water usage was {observed:,.1f} {unit} at {time_str} on {day_name}, which is {pct_dev:+,.1f}% higher than normal "
                    f"({expected:,.1f} {unit}). Since {b_name} is mostly unoccupied at night, water should not be flowing. "
                    f"This is likely caused by a pipe leak, a running toilet, or an open plumbing valve."
                )
            else:
                reason = (
                    f"Water usage rose to {observed:,.1f} {unit} at {time_str} during operating hours, which is {pct_dev:+,.1f}% higher than normal "
                    f"({expected:,.1f} {unit}). This usually happens when multiple restroom fixtures, kitchen dishwashers, "
                    f"or cooling tower water systems run at the same time."
                )

        elif res_key == "electricity":
            if is_off_peak:
                reason = (
                    f"Electricity usage was {observed:,.1f} {unit} at {time_str} on {day_name}, which is {pct_dev:+,.1f}% higher than normal "
                    f"({expected:,.1f} {unit}). Because {b_name} is unoccupied, power use should be low. "
                    f"This usually means heavy lights, computers, or ventilation systems were left running overnight."
                )
            else:
                reason = (
                    f"Electricity usage spiked to {observed:,.1f} {unit} at {time_str} during operating hours, which is {pct_dev:+,.1f}% above normal "
                    f"({expected:,.1f} {unit}). This peak surge usually happens when multiple heavy lab devices, dining appliances, "
                    f"or AC cooling systems start at the same time."
                )

        elif res_key == "waste":
            reason = (
                f"Trash generation reached {observed:,.1f} {unit} on {day_name}, which is {pct_dev:+,.1f}% higher than normal "
                f"({expected:,.1f} {unit}). At {b_name}, this is usually caused by a large campus event, student move-in/out, "
                f"or excess food and packaging boxes."
            )
        else:
            reason = (
                f"{res_key.capitalize()} usage was {observed:,.1f} {unit}, which is {pct_dev:+,.1f}% higher than the normal level of {expected:,.1f} {unit}."
            )

        return {
            "resource": res_key,
            "unit": unit,
            "building_name": b_name,
            "timestamp": timestamp.isoformat(),
            "observed_value": round(observed, 2),
            "expected_value": round(expected, 2),
            "absolute_deviation": abs_dev,
            "deviation_percent": pct_dev,
            "time_of_day": hour,
            "day_of_week": day_name,
            "is_off_peak": is_off_peak,
            "anomaly_score": round(float(anomaly_score), 4),
            "confidence": round(float(anomaly_score), 2),
            "reason": reason,
        }

"""Impact and Savings Measurement Service (Milestone 4B).

Calculates comparable historical baselines, before/after impact metrics,
manages intervention lifecycles, and executes transparent simulation models.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.campus import Building, ResourceMeter, ConsumptionReading, Insight, Intervention


class ImpactService:
    """Service to measure, simulate, and aggregate resource savings and intervention outcomes."""

    RESOURCE_UNITS = {
        "electricity": "kWh",
        "water": "L",
        "waste": "kg",
    }

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 1. Comparable Historical Baseline Methodology
    # ------------------------------------------------------------------
    def calculate_comparable_baseline(
        self,
        resource_type: str,
        building_id: Optional[int] = None,
        building_name: Optional[str] = None,
        event_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculates a scientifically grounded baseline using historical telemetry.

        Methodology:
        1. Entity Scope: Resolves meter(s) for the specific building and resource.
        2. Temporal Context:
           - Hourly (electricity/water): Filters historical readings matching the same hour
             of day (e.g. 14:00) and same day type (weekday vs weekend).
           - Daily (waste): Filters historical readings matching the same day of week.
        3. Anomaly Filtering: Excludes known anomalous readings (is_anomaly == True) to prevent
           skewing the baseline with past pipe leaks or event surges.
        4. Central Tendency: Computes the median or trimmed mean of comparable historical points.
        5. Fallback: If insufficient matching readings exist, uses non-anomalous building mean.
        """
        res_type = resource_type.lower()
        if res_type not in self.RESOURCE_UNITS:
            raise ValueError(f"Unsupported resource type '{resource_type}'")

        # Resolve building_id if only name provided
        if building_id is None and building_name and building_name != "Campus-Wide":
            b = self.db.query(Building).filter(Building.name == building_name).first()
            if b:
                building_id = b.id

        # Query readings
        query = (
            self.db.query(ConsumptionReading.timestamp, ConsumptionReading.value)
            .join(ResourceMeter, ConsumptionReading.meter_id == ResourceMeter.id)
            .filter(ResourceMeter.resource_type == res_type)
            .filter(ConsumptionReading.is_anomaly == False)  # Clean baseline
        )

        if building_id is not None:
            query = query.filter(ResourceMeter.building_id == building_id)

        rows = query.all()
        if not rows:
            return 100.0  # Fallback non-zero positive constant

        df = pd.DataFrame([{"timestamp": r[0], "value": float(r[1])} for r in rows])
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        if event_time is not None:
            dt = pd.to_datetime(event_time)
            is_weekend = dt.weekday() >= 5
            df["is_weekend"] = df["timestamp"].dt.weekday >= 5
            df["hour"] = df["timestamp"].dt.hour
            df["day_of_week"] = df["timestamp"].dt.weekday

            if res_type in ["electricity", "water"]:
                # Match same hour and weekday/weekend profile
                subset = df[(df["hour"] == dt.hour) & (df["is_weekend"] == is_weekend)]
                if len(subset) >= 3:
                    return float(round(subset["value"].median(), 2))
                # Fallback to same hour across all days
                subset_hour = df[df["hour"] == dt.hour]
                if len(subset_hour) >= 3:
                    return float(round(subset_hour["value"].median(), 2))
            else:
                # Waste: match same day of week
                subset = df[df["day_of_week"] == dt.weekday()]
                if len(subset) >= 2:
                    return float(round(subset["value"].median(), 2))

        # Overall building median
        return float(round(df["value"].median(), 2))

    # ------------------------------------------------------------------
    # 2. Reusable Before / After Analysis
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_impact_metrics(
        before_value: float,
        after_value: float,
        baseline_value: float,
    ) -> Dict[str, Any]:
        """
        Reusable before/after calculation with division-by-zero protection
        and explicit negative savings handling.
        """
        b_val = float(before_value)
        a_val = float(after_value)
        base_val = float(baseline_value)

        absolute_reduction = round(b_val - a_val, 2)

        # Division by zero protection
        if b_val > 0:
            raw_savings_pct = round(((b_val - a_val) / b_val) * 100.0, 2)
        else:
            raw_savings_pct = 0.0

        excess_before = max(0.0, round(b_val - base_val, 2))
        excess_after = max(0.0, round(a_val - base_val, 2))
        excess_reduction = round(excess_before - excess_after, 2)

        # Protection: If consumption increased after intervention, do NOT report positive savings
        if a_val > b_val:
            estimated_savings = 0.0
            savings_percentage = 0.0
            status_message = "Consumption increased"
        else:
            estimated_savings = max(0.0, absolute_reduction)
            savings_percentage = max(0.0, raw_savings_pct)
            status_message = "Improvement observed" if estimated_savings > 0 else "No change"

        return {
            "before_value": b_val,
            "after_value": a_val,
            "baseline_value": base_val,
            "absolute_reduction": absolute_reduction,
            "estimated_savings": estimated_savings,
            "savings_percentage": savings_percentage,
            "excess_before": excess_before,
            "excess_after": excess_after,
            "excess_reduction": excess_reduction,
            "impact_status_message": status_message,
        }

    # ------------------------------------------------------------------
    # 3. Simulated Intervention Engine (Transparent Assumption)
    # ------------------------------------------------------------------
    @classmethod
    def simulate_after_value(
        cls,
        before_value: float,
        baseline_value: float,
        simulated_reduction_factor: float = 0.85,
    ) -> float:
        """
        Generates a transparent, documented demo after-value.
        Formula:
          If excess_before > 0:
            after_value = baseline_value + (1.0 - factor) * excess_before
          Else:
            after_value = before_value * (1.0 - factor * 0.10)
        """
        factor = min(1.0, max(0.0, float(simulated_reduction_factor)))
        excess_before = max(0.0, before_value - baseline_value)

        if excess_before > 0:
            # Resolves factor (e.g. 85%) of excess anomaly consumption back toward baseline
            simulated = baseline_value + (1.0 - factor) * excess_before
        else:
            # Already below baseline; small efficiency improvement
            simulated = before_value * (1.0 - (factor * 0.10))

        return round(max(0.0, simulated), 2)

    # ------------------------------------------------------------------
    # 4. Intervention Lifecycle Management
    # ------------------------------------------------------------------
    def create_intervention(
        self,
        insight_id: int,
        action: Optional[str] = None,
        measurement_type: str = "SIMULATED",
    ) -> Intervention:
        """Creates a planned facility intervention from an insight."""
        insight = self.db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            raise ValueError(f"Insight with ID {insight_id} not found")

        # Resolve building
        building_id = None
        if insight.building_name and insight.building_name != "Campus-Wide":
            b = self.db.query(Building).filter(Building.name == insight.building_name).first()
            if b:
                building_id = b.id

        # Determine before and baseline values
        before_val = float(insight.observed_value) if insight.observed_value is not None else 100.0
        if insight.expected_value is not None:
            baseline_val = float(insight.expected_value)
        else:
            baseline_val = self.calculate_comparable_baseline(
                resource_type=insight.resource_type,
                building_id=building_id,
                building_name=insight.building_name,
                event_time=insight.timestamp,
            )

        intervention_action = action or insight.recommended_action or insight.recommendation

        intervention = Intervention(
            insight_id=insight.id,
            resource_type=insight.resource_type,
            building_id=building_id,
            action=intervention_action,
            status="PLANNED",
            started_at=datetime.now(timezone.utc),
            ended_at=None,
            baseline_value=baseline_val,
            before_value=before_val,
            after_value=None,
            estimated_savings=None,
            savings_percentage=None,
            measurement_type=measurement_type.upper(),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(intervention)
        self.db.commit()
        self.db.refresh(intervention)
        return intervention

    def simulate_intervention(
        self,
        intervention_id: int,
        reduction_factor: float = 0.85,
    ) -> Intervention:
        """Simulates completion of an intervention with transparent demo assumptions."""
        itv = self.db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not itv:
            raise ValueError(f"Intervention with ID {intervention_id} not found")

        before_val = itv.before_value if itv.before_value is not None else 100.0
        baseline_val = itv.baseline_value if itv.baseline_value is not None else 80.0

        after_val = self.simulate_after_value(
            before_value=before_val,
            baseline_value=baseline_val,
            simulated_reduction_factor=reduction_factor,
        )

        metrics = self.calculate_impact_metrics(
            before_value=before_val,
            after_value=after_val,
            baseline_value=baseline_val,
        )

        itv.after_value = metrics["after_value"]
        itv.estimated_savings = metrics["estimated_savings"]
        itv.savings_percentage = metrics["savings_percentage"]
        itv.status = "COMPLETED"
        itv.measurement_type = "SIMULATED"
        itv.ended_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(itv)
        return itv

    def complete_intervention(
        self,
        intervention_id: int,
        after_value: Optional[float] = None,
    ) -> Intervention:
        """Marks an intervention as completed using either measured or simulated data."""
        itv = self.db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not itv:
            raise ValueError(f"Intervention with ID {intervention_id} not found")

        before_val = itv.before_value if itv.before_value is not None else 100.0
        baseline_val = itv.baseline_value if itv.baseline_value is not None else 80.0

        if after_value is not None:
            # Physical measurement provided
            a_val = float(after_value)
            m_type = "MEASURED"
        elif itv.after_value is not None:
            # Already calculated/simulated
            a_val = float(itv.after_value)
            m_type = itv.measurement_type
        else:
            # Fallback to simulation
            a_val = self.simulate_after_value(before_val, baseline_val, 0.85)
            m_type = "SIMULATED"

        metrics = self.calculate_impact_metrics(
            before_value=before_val,
            after_value=a_val,
            baseline_value=baseline_val,
        )

        itv.after_value = metrics["after_value"]
        itv.estimated_savings = metrics["estimated_savings"]
        itv.savings_percentage = metrics["savings_percentage"]
        itv.status = "COMPLETED"
        itv.measurement_type = m_type
        itv.ended_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(itv)
        return itv

    def get_interventions(
        self,
        resource: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves history of interventions with computed excess metrics."""
        query = self.db.query(Intervention)
        if resource:
            query = query.filter(Intervention.resource_type == resource.lower())
        if status:
            query = query.filter(Intervention.status == status.upper())

        itvs = query.order_by(Intervention.created_at.desc()).all()
        results = []
        for itv in itvs:
            b_name = itv.building.name if itv.building else "Campus-Wide"
            unit = self.RESOURCE_UNITS.get(itv.resource_type.lower(), "")

            # Compute excess metrics if values are available
            excess_before = None
            excess_after = None
            excess_reduction = None
            msg = None

            if itv.before_value is not None and itv.baseline_value is not None:
                excess_before = max(0.0, round(itv.before_value - itv.baseline_value, 2))
                if itv.after_value is not None:
                    excess_after = max(0.0, round(itv.after_value - itv.baseline_value, 2))
                    excess_reduction = round(excess_before - excess_after, 2)
                    msg = "Consumption increased" if itv.after_value > itv.before_value else "Improvement observed"

            results.append({
                "id": itv.id,
                "insight_id": itv.insight_id,
                "resource_type": itv.resource_type,
                "building_id": itv.building_id,
                "building_name": b_name,
                "action": itv.action,
                "status": itv.status,
                "started_at": itv.started_at.isoformat() if itv.started_at else None,
                "ended_at": itv.ended_at.isoformat() if itv.ended_at else None,
                "baseline_value": itv.baseline_value,
                "before_value": itv.before_value,
                "after_value": itv.after_value,
                "estimated_savings": itv.estimated_savings,
                "savings_percentage": itv.savings_percentage,
                "excess_before": excess_before,
                "excess_after": excess_after,
                "excess_reduction": excess_reduction,
                "measurement_type": itv.measurement_type,
                "created_at": itv.created_at.isoformat() if itv.created_at else None,
                "unit": unit,
                "impact_status_message": msg,
            })
        return results

    def get_intervention_by_id(self, intervention_id: int) -> Dict[str, Any]:
        """Retrieves a single intervention by ID."""
        itv = self.db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not itv:
            raise ValueError(f"Intervention with ID {intervention_id} not found")

        b_name = itv.building.name if itv.building else "Campus-Wide"
        unit = self.RESOURCE_UNITS.get(itv.resource_type.lower(), "")

        excess_before = None
        excess_after = None
        excess_reduction = None
        msg = None

        if itv.before_value is not None and itv.baseline_value is not None:
            excess_before = max(0.0, round(itv.before_value - itv.baseline_value, 2))
            if itv.after_value is not None:
                excess_after = max(0.0, round(itv.after_value - itv.baseline_value, 2))
                excess_reduction = round(excess_before - excess_after, 2)
                msg = "Consumption increased" if itv.after_value > itv.before_value else "Improvement observed"

        return {
            "id": itv.id,
            "insight_id": itv.insight_id,
            "resource_type": itv.resource_type,
            "building_id": itv.building_id,
            "building_name": b_name,
            "action": itv.action,
            "status": itv.status,
            "started_at": itv.started_at.isoformat() if itv.started_at else None,
            "ended_at": itv.ended_at.isoformat() if itv.ended_at else None,
            "baseline_value": itv.baseline_value,
            "before_value": itv.before_value,
            "after_value": itv.after_value,
            "estimated_savings": itv.estimated_savings,
            "savings_percentage": itv.savings_percentage,
            "excess_before": excess_before,
            "excess_after": excess_after,
            "excess_reduction": excess_reduction,
            "measurement_type": itv.measurement_type,
            "created_at": itv.created_at.isoformat() if itv.created_at else None,
            "unit": unit,
            "impact_status_message": msg,
        }

    # ------------------------------------------------------------------
    # 5. Aggregate Impact Summary
    # ------------------------------------------------------------------
    def get_impact_summary(self) -> Dict[str, Any]:
        """
        Calculates aggregate campus resource savings across all completed interventions.
        Retains native units and determines if metrics are SIMULATED, MEASURED, or MIXED.
        """
        completed = self.db.query(Intervention).filter(Intervention.status == "COMPLETED").all()
        all_itvs = self.db.query(Intervention).all()

        measurement_types = set(i.measurement_type for i in completed)
        if not measurement_types:
            overall_type = "SIMULATED"
        elif len(measurement_types) == 1:
            overall_type = list(measurement_types)[0]
        else:
            overall_type = "MIXED"

        summary_by_res = {}
        for res, unit in self.RESOURCE_UNITS.items():
            res_completed = [i for i in completed if i.resource_type.lower() == res]
            res_total = [i for i in all_itvs if i.resource_type.lower() == res]

            total_savings = sum(i.estimated_savings or 0.0 for i in res_completed)
            pcts = [i.savings_percentage for i in res_completed if i.savings_percentage is not None]
            avg_pct = float(round(np.mean(pcts), 2)) if pcts else 0.0

            summary_by_res[res] = {
                "total_estimated_savings": float(round(total_savings, 2)),
                "unit": unit,
                "average_improvement_percent": avg_pct,
                "total_interventions": len(res_total),
                "completed_interventions": len(res_completed),
            }

        return {
            "water": summary_by_res["water"],
            "electricity": summary_by_res["electricity"],
            "waste": summary_by_res["waste"],
            "overall_measurement_type": overall_type,
            "total_completed_interventions": len(completed),
            "disclaimer": "SIMULATED DEMO IMPACT: Results generated from documented simulation models because the prototype environment does not have real-time physical actuators.",
        }

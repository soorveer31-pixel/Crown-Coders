"""Resource Service Module.

Handles business logic for aggregating and querying campus telemetry data
across electricity, water, and waste streams using SQLAlchemy.
"""

from datetime import timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campus import ResourceMeter, ConsumptionReading


class ResourceService:
    """Service class for campus utility and waste telemetry operations."""

    SUPPORTED_RESOURCES: List[str] = ["electricity", "water", "waste"]
    SUPPORTED_RANGES: List[str] = ["7d", "30d"]
    RESOURCE_UNITS: Dict[str, str] = {
        "electricity": "kWh",
        "water": "L",
        "waste": "kg",
    }

    def __init__(self, db: Session):
        self.db = db

    def get_supported_resources(self) -> List[str]:
        """Returns the list of monitored campus resource categories."""
        return self.SUPPORTED_RESOURCES

    def get_resource_summary(self) -> Dict[str, Any]:
        """Calculates aggregated telemetry metrics across all 3 resource streams.

        Returns:
            Dictionary with current rate, historical average, and total consumption
            for electricity, water, and waste.
        """
        summary = {}

        for resource in self.SUPPORTED_RESOURCES:
            unit = self.RESOURCE_UNITS[resource]

            # Fetch all meters for this resource
            meters = (
                self.db.query(ResourceMeter.id)
                .filter(ResourceMeter.resource_type == resource)
                .all()
            )
            meter_ids = [m.id for m in meters]

            if not meter_ids:
                summary[resource] = {
                    "current": 0.0,
                    "average": 0.0,
                    "total": 0.0,
                    "unit": unit,
                }
                continue

            # 1. Total consumption
            total_val = (
                self.db.query(func.sum(ConsumptionReading.value))
                .filter(ConsumptionReading.meter_id.in_(meter_ids))
                .scalar()
                or 0.0
            )

            # 2. Latest timestamp and current rate
            latest_ts = (
                self.db.query(func.max(ConsumptionReading.timestamp))
                .filter(ConsumptionReading.meter_id.in_(meter_ids))
                .scalar()
            )

            current_val = 0.0
            if latest_ts:
                current_val = (
                    self.db.query(func.sum(ConsumptionReading.value))
                    .filter(
                        ConsumptionReading.meter_id.in_(meter_ids),
                        ConsumptionReading.timestamp == latest_ts,
                    )
                    .scalar()
                    or 0.0
                )

            # 3. Average campus rate per timestep
            subquery = (
                self.db.query(
                    ConsumptionReading.timestamp,
                    func.sum(ConsumptionReading.value).label("step_total"),
                )
                .filter(ConsumptionReading.meter_id.in_(meter_ids))
                .group_by(ConsumptionReading.timestamp)
                .subquery()
            )

            avg_val = self.db.query(func.avg(subquery.c.step_total)).scalar() or 0.0

            summary[resource] = {
                "current": round(float(current_val), 2),
                "average": round(float(avg_val), 2),
                "total": round(float(total_val), 2),
                "unit": unit,
            }

        return summary

    def get_resource_history(self, resource: str, range_str: str = "7d") -> Dict[str, Any]:
        """Retrieves time-series data grouped by timestamp for the selected range.

        Args:
            resource: One of 'electricity', 'water', or 'waste'.
            range_str: One of '7d' or '30d'.

        Returns:
            Dictionary containing resource type, unit, and ordered time-series points.
        """
        res_key = resource.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(
                f"Invalid resource '{resource}'. Supported resources are: {', '.join(self.SUPPORTED_RESOURCES)}"
            )

        range_key = range_str.lower().strip()
        if range_key not in self.SUPPORTED_RANGES:
            raise ValueError(
                f"Invalid range '{range_str}'. Supported ranges are: {', '.join(self.SUPPORTED_RANGES)}"
            )

        unit = self.RESOURCE_UNITS[res_key]
        days = 7 if range_key == "7d" else 30

        # Query max timestamp for this resource to calculate relative time window
        latest_ts = (
            self.db.query(func.max(ConsumptionReading.timestamp))
            .join(ResourceMeter, ConsumptionReading.meter_id == ResourceMeter.id)
            .filter(ResourceMeter.resource_type == res_key)
            .scalar()
        )

        if not latest_ts:
            return {
                "resource": res_key,
                "unit": unit,
                "range": range_key,
                "data": [],
            }

        cutoff = latest_ts - timedelta(days=days)

        results = (
            self.db.query(
                ConsumptionReading.timestamp,
                func.sum(ConsumptionReading.value).label("total_value"),
            )
            .join(ResourceMeter, ConsumptionReading.meter_id == ResourceMeter.id)
            .filter(
                ResourceMeter.resource_type == res_key,
                ConsumptionReading.timestamp >= cutoff,
            )
            .group_by(ConsumptionReading.timestamp)
            .order_by(ConsumptionReading.timestamp.asc())
            .all()
        )

        data = [
            {
                "timestamp": row.timestamp.isoformat(),
                "value": round(float(row.total_value), 2),
            }
            for row in results
        ]

        return {
            "resource": res_key,
            "unit": unit,
            "range": range_key,
            "data": data,
        }

"""SQLAlchemy models for campus buildings, resource meters, and consumption readings."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def get_utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Building(Base):
    """Represents a physical facility on campus."""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=False)
    sqft = Column(Integer, nullable=False)

    # Relationships
    meters = relationship("ResourceMeter", back_populates="building", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Building(id={self.id}, name='{self.name}', type='{self.type}')>"


class ResourceMeter(Base):
    """Represents a dedicated resource meter (electricity, water, or waste) for a building."""
    __tablename__ = "resource_meters"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)  # 'electricity', 'water', 'waste'
    unit = Column(String, nullable=False)  # 'kWh', 'L', 'kg'

    # Relationships
    building = relationship("Building", back_populates="meters")
    readings = relationship("ConsumptionReading", back_populates="meter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResourceMeter(id={self.id}, building_id={self.building_id}, resource='{self.resource_type}')>"


class ConsumptionReading(Base):
    """Represents a discrete consumption record logged by a meter."""
    __tablename__ = "consumption_readings"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("resource_meters.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    meter = relationship("ResourceMeter", back_populates="readings")
    predictions = relationship("AnomalyPrediction", back_populates="reading", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_meter_timestamp", "meter_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ConsumptionReading(id={self.id}, meter_id={self.meter_id}, ts={self.timestamp}, val={self.value})>"


class AnomalyPrediction(Base):
    """Stores machine learning model anomaly predictions without altering ground-truth labels."""
    __tablename__ = "anomaly_predictions"

    id = Column(Integer, primary_key=True, index=True)
    reading_id = Column(Integer, ForeignKey("consumption_readings.id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    predicted_anomaly = Column(Boolean, nullable=False, index=True)
    model_version = Column(String, default="isolation_forest_v1.0", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    reading = relationship("ConsumptionReading", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<AnomalyPrediction(id={self.id}, reading_id={self.reading_id}, score={self.anomaly_score}, pred={self.predicted_anomaly})>"


class Insight(Base):
    """Stores generated anomaly explanations and forecast-based proactive recommendations."""
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, nullable=False, index=True)
    building_name = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    insight_type = Column(String, nullable=False)  # 'anomaly' or 'forecast_risk'
    severity = Column(String, nullable=False)      # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    priority_score = Column(Float, nullable=False)
    title = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)
    observed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    interventions = relationship("Intervention", back_populates="insight", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, type='{self.insight_type}', sev='{self.severity}', title='{self.title}')>"


class Intervention(Base):
    """Represents a planned, in-progress, or completed facility intervention based on an insight."""
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)  # 'electricity', 'water', 'waste'
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False)
    status = Column(String, default="PLANNED", nullable=False, index=True)  # 'PLANNED', 'IN_PROGRESS', 'COMPLETED'
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    baseline_value = Column(Float, nullable=True)
    before_value = Column(Float, nullable=True)
    after_value = Column(Float, nullable=True)
    estimated_savings = Column(Float, nullable=True)
    savings_percentage = Column(Float, nullable=True)
    measurement_type = Column(String, default="SIMULATED", nullable=False, index=True)  # 'SIMULATED', 'MEASURED'
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    insight = relationship("Insight", back_populates="interventions")
    building = relationship("Building")

    def __repr__(self) -> str:
        return f"<Intervention(id={self.id}, insight_id={self.insight_id}, status='{self.status}', type='{self.measurement_type}')>"




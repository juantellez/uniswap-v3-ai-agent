# models/metric.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PositionMetric(Base):
    __tablename__ = "position_metrics"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    
    # Métricas calculadas
    price_lower = Column(Float)
    price_upper = Column(Float)
    current_price = Column(Float)
    is_in_range = Column(Boolean)
    
    # ... aquí añadiremos más métricas como IL, APR, etc.
    
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())
    
    position = relationship("Position", back_populates="metrics")
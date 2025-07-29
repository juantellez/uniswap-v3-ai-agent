# src/models/metric.py
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PositionMetric(Base):
    __tablename__ = "position_metrics"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    
    price_lower = Column(Float)
    price_upper = Column(Float)
    current_price = Column(Float)
    is_in_range = Column(Boolean)
    
    impermanent_loss_percent = Column(Float, nullable=True, default=0.0)
    
    unclaimed_fees_usd = Column(Float, nullable=True, default=0.0)
    real_apr_percent = Column(Float, nullable=True, default=0.0)
    
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())
    
    position = relationship("Position", back_populates="metrics")
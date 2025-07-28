# models/recommendation.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("position_metrics.id"), nullable=False, unique=True)
    
    # Salida del modelo IA
    recommendation_action = Column(String) # Ej: "MAINTAIN", "REBALANCE", "CLOSE"
    justification = Column(Text)
    raw_model_output = Column(Text) # Guardamos la respuesta completa del modelo para auditoría
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    metric = relationship("PositionMetric")
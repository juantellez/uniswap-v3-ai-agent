# models/position.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, unique=True, nullable=False, index=True) # NFT ID de la posición V3
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    
    # Datos descriptivos del pool
    pool_address = Column(String, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token1_symbol = Column(String, nullable=False)
    
    # Rango de la posición
    tick_lower = Column(String)
    tick_upper = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    wallet = relationship("Wallet")
    metrics = relationship("PositionMetric", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(token_id={self.token_id}, pool='{self.token0_symbol}/{self.token1_symbol}')>"
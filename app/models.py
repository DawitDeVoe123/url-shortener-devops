from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from app.database import Base

class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(50), unique=True, index=True, nullable=False)  # Changed from 10 to 50
    original_url = Column(String(500), nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    clicks = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)

class Click(Base):
    __tablename__ = "clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    referer = Column(String(500))
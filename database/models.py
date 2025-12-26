"""
Database Models
SQLAlchemy ORM Models
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, 
    DateTime, Boolean, Float, Text, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import DATABASE_PATH

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=True)
    username = Column(String(100))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    tests = relationship("Test", back_populates="user")

class Test(Base):
    """Test model"""
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(String(50), unique=True)
    video_url = Column(Text)
    view_count = Column(Integer)
    views_sent = Column(Integer, default=0)
    views_failed = Column(Integer, default=0)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="tests")

class TikTokAccount(Base):
    """TikTok account model"""
    __tablename__ = 'tiktok_accounts'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(100))
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(20), default='active')  # active, banned, limited
    last_used = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

class Proxy(Base):
    """Proxy model"""
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True)
    proxy_url = Column(String(500), unique=True)
    proxy_type = Column(String(10))  # http, https, socks4, socks5
    country = Column(String(50), nullable=True)
    speed = Column(Float, nullable=True)  # in milliseconds
    success_rate = Column(Float, default=0.0)
    last_used = Column(DateTime, nullable=True)
    last_tested = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    """System log model"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(10))  # info, warning, error, critical
    module = Column(String(100))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create database engine
engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
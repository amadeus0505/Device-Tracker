from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnownDevice(Base):
    __tablename__ = "known_devices"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String(128), nullable=False)
    mac = Column(String(32), index=True, nullable=True)
    ip = Column(String(64), nullable=True)
    dhcp_fingerprint = Column(Text, index=True, nullable=False)
    connected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    events = relationship("ConnectionEvent", back_populates="device")


class ConnectionEvent(Base):
    __tablename__ = "connection_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("known_devices.id"), nullable=False)
    mac = Column(String(32), nullable=False)
    ip = Column(String(64), nullable=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    device = relationship("KnownDevice", back_populates="events")

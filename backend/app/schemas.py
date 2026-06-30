from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    owner_name: str
    dhcp_fingerprint: str
    mac: Optional[str] = None
    ip: Optional[str] = None


class DeviceUpdate(BaseModel):
    owner_name: Optional[str] = None
    dhcp_fingerprint: Optional[str] = None
    mac: Optional[str] = None
    ip: Optional[str] = None
    connected: Optional[bool] = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_name: str
    mac: Optional[str]
    ip: Optional[str]
    dhcp_fingerprint: str
    connected: bool
    created_at: datetime
    updated_at: datetime


class ConnectionEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    mac: str
    ip: Optional[str]
    connected_at: datetime
    disconnected_at: Optional[datetime] = None


class UnknownConnectedDevice(BaseModel):
    mac: str
    ip: Optional[str] = None
    first_seen_at: datetime
    connected_since_seconds: int = Field(..., ge=0)
    connected_since_label: str
    current_fingerprint: Optional[str] = None


class DeviceOverview(BaseModel):
    known_devices: list[DeviceRead]
    unknown_connected_devices: list[UnknownConnectedDevice]
    connected_known_devices: list[DeviceRead]

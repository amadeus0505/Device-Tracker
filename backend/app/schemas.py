from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    owner_name: str = Field(min_length=1, max_length=128)
    dhcp_fingerprint: str = Field(min_length=1)
    mac: str | None = None
    ip: str | None = None


class DeviceUpdate(BaseModel):
    owner_name: str | None = None
    dhcp_fingerprint: str | None = None
    mac: str | None = None
    ip: str | None = None
    connected: bool | None = None


class DeviceRead(BaseModel):
    id: int
    owner_name: str
    mac: str | None = None
    ip: str | None = None
    dhcp_fingerprint: str
    connected: bool

    class Config:
        from_attributes = True


class DeviceEventRead(BaseModel):
    id: int
    device_id: int
    mac: str
    ip: str | None = None
    connected_at: str
    disconnected_at: str | None = None

    class Config:
        from_attributes = True


class DeviceStats(BaseModel):
    device_id: int
    owner_name: str
    connected: bool
    total_sessions: int
    recent_sessions_7: int
    recent_sessions_30: int
    total_minutes_connected: int
    last_seen: str | None = None

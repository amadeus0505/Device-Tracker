from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    owner_name: str
    dhcp_fingerprint: str
    mac: str | None = None
    ip: str | None = None


class DeviceRead(BaseModel):
    id: int
    owner_name: str
    mac: str | None = None
    ip: str | None = None
    dhcp_fingerprint: str
    connected: bool

    class Config:
        from_attributes = True


class DeviceStats(BaseModel):
    device_id: int
    owner_name: str
    connected: bool
    total_sessions: int
    recent_sessions: int
    total_minutes_connected: int

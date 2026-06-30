import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token, verify_password
from app.crud import create_device, create_user, seed_defaults, update_device
from app.models import KnownDevice, User
from app.schemas import DeviceCreate, DeviceRead, DeviceStats, DeviceUpdate, Token, UserCreate, UserRead
from app.services import device_stats_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("device_tracker")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_event(message: str, **extra):
    payload = " ".join(f"{k}={v}" for k, v in extra.items())
    logger.info("%s %s", message, payload)


@app.on_event("startup")
def startup() -> None:
    db = SessionLocal()
    try:
        log_event("startup.begin", db_path=str(engine.url.database))
        seed_defaults(db)
        log_event("startup.seeded")
    finally:
        db.close()


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    log_event("auth.login.attempt", username=form_data.username)
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        log_event("auth.login.failed", username=form_data.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "admin": user.is_admin, "iat": datetime.now(timezone.utc).timestamp()})
    log_event("auth.login.success", username=user.username, admin=user.is_admin)
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserRead)
def me(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        log_event("auth.me.unauthorized")
        raise HTTPException(status_code=401, detail="Not authenticated")
    log_event("auth.me.success", username=user.username)
    return user


@app.post("/admin/users", response_model=UserRead)
def add_user(user_in: UserCreate, db: Session = Depends(get_db)):
    log_event("admin.user.create", username=user_in.username, admin=user_in.is_admin)
    return create_user(db, user_in)


@app.get("/admin/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    log_event("admin.user.list", count=len(users))
    return users


@app.get("/devices", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(KnownDevice).order_by(KnownDevice.created_at.desc()).all()
    log_event("devices.list", count=len(devices))
    return devices


@app.post("/devices", response_model=DeviceRead)
def add_device(device_in: DeviceCreate, db: Session = Depends(get_db)):
    log_event("devices.create", owner=device_in.owner_name, has_mac=bool(device_in.mac), has_ip=bool(device_in.ip))
    return create_device(db, device_in)


@app.put("/devices/{device_id}", response_model=DeviceRead)
def edit_device(device_id: int, device_in: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(KnownDevice).filter(KnownDevice.id == device_id).first()
    if not device:
        log_event("devices.update.not_found", device_id=device_id)
        raise HTTPException(status_code=404, detail="Device not found")
    log_event("devices.update", device_id=device_id)
    return update_device(db, device, device_in.model_dump())


@app.get("/devices/{device_id}/stats")
def read_device_stats(device_id: int, db: Session = Depends(get_db)):
    device = db.query(KnownDevice).filter(KnownDevice.id == device_id).first()
    if not device:
        log_event("devices.stats.not_found", device_id=device_id)
        raise HTTPException(status_code=404, detail="Device not found")
    stats = device_stats_service.stats(db, device)
    log_event("devices.stats", device_id=device_id, sessions=stats["total_sessions"], connected=stats["connected"])
    return stats

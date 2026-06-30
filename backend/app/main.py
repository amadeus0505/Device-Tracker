from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token, verify_password
from app.crud import create_device, create_user, seed_defaults
from app.models import KnownDevice, User
from app.schemas import DeviceCreate, DeviceRead, DeviceStats, Token, UserCreate, UserRead
from app.services import device_stats_service

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.on_event("startup")
def startup() -> None:
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "admin": user.is_admin, "iat": datetime.now(timezone.utc).timestamp()})
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserRead)
def me(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.post("/admin/users", response_model=UserRead)
def add_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)


@app.get("/admin/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@app.get("/devices", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db)):
    return db.query(KnownDevice).order_by(KnownDevice.created_at.desc()).all()


@app.post("/devices", response_model=DeviceRead)
def add_device(device_in: DeviceCreate, db: Session = Depends(get_db)):
    return create_device(db, device_in)


@app.get("/devices/{device_id}/stats", response_model=DeviceStats)
def read_device_stats(device_id: int, db: Session = Depends(get_db)):
    device = db.query(KnownDevice).filter(KnownDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_stats_service.stats(db, device)

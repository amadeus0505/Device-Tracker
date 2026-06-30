from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal
from app.crud import create_device, create_user, seed_defaults
from app.models import KnownDevice, User
from app.schemas import DeviceCreate, DeviceRead, DeviceStats, Token, UserCreate, UserRead
from app.services import device_stats

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Tracker API")


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
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token="dev-token")


@app.post("/admin/users", response_model=UserRead)
def add_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)


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
    return device_stats(db, device)

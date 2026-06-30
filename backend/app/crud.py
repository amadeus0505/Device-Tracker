from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import KnownDevice, User
from app.schemas import DeviceCreate, UserCreate


DEFAULT_DEVICES = [
    ("Eder", "1,2,6,12,15,26,28,121,3,33,40,41,42,119,249,252,17"),
    ("Flo", "1,3,28,6"),
    ("Gabriel-Oneplus", "1,3,6,15,26,28,51,58,59,43,114,108"),
    ("Gabriel-Surface", "1,3,6,15,31,33,43,44,46,47,119,121,249,252"),
]


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_admin=user_in.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_device(db: Session, device_in: DeviceCreate) -> KnownDevice:
    device = KnownDevice(
        owner_name=device_in.owner_name,
        dhcp_fingerprint=device_in.dhcp_fingerprint,
        mac=device_in.mac,
        ip=device_in.ip,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device(db: Session, device: KnownDevice, data: dict) -> KnownDevice:
    for key, value in data.items():
        if value is not None and hasattr(device, key):
            setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


def seed_defaults(db: Session) -> None:
    if not db.query(User).first():
        create_user(db, UserCreate(username="admin", password="admin1234", is_admin=True))
    if not db.query(KnownDevice).first():
        for owner_name, fp in DEFAULT_DEVICES:
            db.add(KnownDevice(owner_name=owner_name, dhcp_fingerprint=fp, connected=False))
        db.commit()

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import ConnectionEvent, KnownDevice


class DeviceStatsService:
    @staticmethod
    def mark_connected(db: Session, device: KnownDevice, mac: str, ip: str | None = None) -> ConnectionEvent:
        device.connected = True
        device.mac = mac
        if ip:
            device.ip = ip
        event = ConnectionEvent(device_id=device.id, mac=mac, ip=ip)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def mark_disconnected(db: Session, device: KnownDevice) -> None:
        device.connected = False
        event = (
            db.query(ConnectionEvent)
            .filter(ConnectionEvent.device_id == device.id, ConnectionEvent.disconnected_at.is_(None))
            .order_by(ConnectionEvent.connected_at.desc())
            .first()
        )
        if event:
            event.disconnected_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def stats(db: Session, device: KnownDevice) -> dict:
        now = datetime.now(timezone.utc)
        recent_cutoff_7 = now - timedelta(days=7)
        recent_cutoff_30 = now - timedelta(days=30)
        events = db.query(ConnectionEvent).filter(ConnectionEvent.device_id == device.id).all()
        total_sessions = len(events)
        recent_sessions_7 = sum(1 for e in events if e.connected_at and e.connected_at >= recent_cutoff_7)
        recent_sessions_30 = sum(1 for e in events if e.connected_at and e.connected_at >= recent_cutoff_30)
        total_minutes = 0
        last_seen = None
        for e in events:
            if e.connected_at and (last_seen is None or e.connected_at > last_seen):
                last_seen = e.connected_at
            end = e.disconnected_at or now
            if e.connected_at:
                total_minutes += int((end - e.connected_at).total_seconds() // 60)
        return {
            "device_id": device.id,
            "owner_name": device.owner_name,
            "connected": device.connected,
            "total_sessions": total_sessions,
            "recent_sessions_7": recent_sessions_7,
            "recent_sessions_30": recent_sessions_30,
            "total_minutes_connected": total_minutes,
            "last_seen": last_seen.isoformat() if last_seen else None,
        }


device_stats_service = DeviceStatsService()

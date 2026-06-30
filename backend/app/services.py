from datetime import datetime, timezone

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
    def active_known_devices(db: Session) -> list[KnownDevice]:
        return db.query(KnownDevice).filter(KnownDevice.connected.is_(True)).order_by(KnownDevice.updated_at.desc()).all()

    @staticmethod
    def unknown_connected_devices(db: Session) -> list[dict]:
        connected = (
            db.query(ConnectionEvent)
            .filter(ConnectionEvent.disconnected_at.is_(None))
            .order_by(ConnectionEvent.connected_at.desc())
            .all()
        )
        unknown: list[dict] = []
        known_macs = {d.mac for d in db.query(KnownDevice.mac).filter(KnownDevice.mac.isnot(None)).all()}
        now = datetime.now(timezone.utc)
        for event in connected:
            mac = event.mac
            if not mac or mac in known_macs:
                continue
            connected_since = event.connected_at or now
            seconds = max(0, int((now - connected_since).total_seconds()))
            label = DeviceStatsService._format_duration(seconds)
            unknown.append(
                {
                    "mac": mac,
                    "ip": event.ip,
                    "first_seen_at": connected_since,
                    "connected_since_seconds": seconds,
                    "connected_since_label": label,
                    "current_fingerprint": None,
                }
            )
        deduped: list[dict] = []
        seen = set()
        for item in unknown:
            if item["mac"] in seen:
                continue
            seen.add(item["mac"])
            deduped.append(item)
        return deduped

    @staticmethod
    def _format_duration(seconds: int) -> str:
        minutes, _ = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m"
        return f"{seconds}s"

    @staticmethod
    def stats(db: Session, device: KnownDevice) -> dict:
        now = datetime.now(timezone.utc)
        events = db.query(ConnectionEvent).filter(ConnectionEvent.device_id == device.id).all()
        total_sessions = len(events)
        recent_sessions_7 = sum(1 for e in events if e.connected_at and (now - e.connected_at).days < 7)
        recent_sessions_30 = sum(1 for e in events if e.connected_at and (now - e.connected_at).days < 30)
        total_minutes = 0
        last_seen = None
        history = []
        for e in events:
            if e.connected_at and (last_seen is None or e.connected_at > last_seen):
                last_seen = e.connected_at
            end = e.disconnected_at or now
            if e.connected_at:
                total_minutes += int((end - e.connected_at).total_seconds() // 60)
            history.append(
                {
                    "id": e.id,
                    "device_id": e.device_id,
                    "mac": e.mac,
                    "ip": e.ip,
                    "connected_at": e.connected_at.isoformat() if e.connected_at else None,
                    "disconnected_at": e.disconnected_at.isoformat() if e.disconnected_at else None,
                }
            )
        return {
            "device_id": device.id,
            "owner_name": device.owner_name,
            "connected": device.connected,
            "total_sessions": total_sessions,
            "recent_sessions_7": recent_sessions_7,
            "recent_sessions_30": recent_sessions_30,
            "total_minutes_connected": total_minutes,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "history": history,
        }


device_stats_service = DeviceStatsService()

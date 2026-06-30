from scapy.all import BOOTP, DHCP, sniff

from app.core.database import SessionLocal
from app.models import KnownDevice
from app.services import device_stats_service


class NetworkDetector:
    def __init__(self, db_factory=SessionLocal):
        self.db_factory = db_factory

    def check_known_device(self, fp: str):
        db = self.db_factory()
        try:
            device = db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == fp).first()
            print(f"[detector] lookup fp={fp!r} found={bool(device)}")
            return device
        finally:
            db.close()

    def handle_dhcp_packet(self, pkt):
        if BOOTP not in pkt or DHCP not in pkt:
            print("[detector] skipped non-DHCP packet")
            return
        raw_mac = pkt[BOOTP].chaddr.hex()[:12]
        mac = ":".join(raw_mac[i:i + 2] for i in range(0, 12, 2))
        for opt in pkt[DHCP].options:
            if isinstance(opt, tuple) and opt[0] == "param_req_list":
                fp = ",".join(str(b) for b in opt[1])
                print(f"[detector] dhcp packet mac={mac} fp={fp}")
                db = self.db_factory()
                try:
                    device = db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == fp).first()
                    if device:
                        print(f"[detector] match device_id={device.id} owner={device.owner_name}")
                        device_stats_service.mark_connected(db, device, mac)
                    else:
                        print("[detector] no device match")
                finally:
                    db.close()

    def sniff_dhcp(self):
        print("[detector] sniffing dhcp on host interface")
        sniff(filter="udp and (port 67 or port 68)", prn=self.handle_dhcp_packet, store=0)


def run_detector():
    NetworkDetector().sniff_dhcp()

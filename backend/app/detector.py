from scapy.all import ARP, BOOTP, DHCP, Ether, sniff, srp

from app.core.database import SessionLocal
from app.models import KnownDevice
from app.services import device_stats_service


class NetworkDetector:
    def __init__(self, db_factory=SessionLocal):
        self.db_factory = db_factory

    def check_known_device(self, fp: str):
        db = self.db_factory()
        try:
            return db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == fp).first()
        finally:
            db.close()

    def handle_dhcp_packet(self, pkt):
        raw_mac = pkt[BOOTP].chaddr.hex()[:12]
        mac = ":".join(raw_mac[i:i + 2] for i in range(0, 12, 2))
        for opt in pkt[DHCP].options:
            if isinstance(opt, tuple) and opt[0] == "param_req_list":
                fp = ",".join(str(b) for b in opt[1])
                db = self.db_factory()
                try:
                    device = db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == fp).first()
                    if device:
                        device_stats_service.mark_connected(db, device, mac)
                finally:
                    db.close()

    def sniff_dhcp(self):
        sniff(filter="udp and (port 67 or port 68)", prn=self.handle_dhcp_packet, store=0)


def run_detector():
    NetworkDetector().sniff_dhcp()

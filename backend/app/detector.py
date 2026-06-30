from scapy.all import ARP, BOOTP, DHCP, Ether, srp, sniff

from app.core.database import SessionLocal
from app.models import KnownDevice
from app.services import device_stats_service


KNOWN_OPTION_ORDER = [1, 3, 6, 15, 26, 28, 51, 58, 59, 43, 114, 108, 31, 33, 40, 41, 42, 44, 46, 47, 119, 121, 249, 252, 17]


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

    def build_fingerprint(self, pkt) -> str:
        for opt in pkt[DHCP].options:
            if isinstance(opt, tuple) and opt[0] == "param_req_list":
                values = [int(b) for b in opt[1]]
                fp = ",".join(str(b) for b in values)
                print(f"[detector] extracted fingerprint={fp}")
                return fp
        print(f"[detector] no param_req_list found; options={pkt[DHCP].options}")
        return ""

    def handle_dhcp_packet(self, pkt):
        if BOOTP not in pkt or DHCP not in pkt:
            print("[detector] skipped non-DHCP packet")
            return
        raw_mac = pkt[BOOTP].chaddr.hex()[:12]
        mac = ":".join(raw_mac[i:i + 2] for i in range(0, 12, 2))
        fp = self.build_fingerprint(pkt)
        if not fp:
            return
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

    def active_arp_check(self, device: KnownDevice):
        if not device.mac:
            print(f"[detector] arp check skipped device_id={device.id} no mac")
            return False
        network = device.ip if device.ip is not None else "10.0.0.0/24"
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
        answered, _ = srp(pkt, timeout=2, verbose=False)
        for _, rcv in answered:
            if rcv.hwsrc == device.mac:
                if device.ip is None:
                    device.ip = rcv.psrc
                return True
        return False

    def sniff_dhcp(self):
        print("[detector] sniffing dhcp on host interface")
        sniff(filter="udp and (port 67 or port 68)", prn=self.handle_dhcp_packet, store=0)


def run_detector():
    NetworkDetector().sniff_dhcp()

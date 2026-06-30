import random
import threading
import time

from scapy.all import ARP, BOOTP, DHCP, Ether, srp, sniff

from app.core.database import SessionLocal
from app.models import KnownDevice
from app.services import device_stats_service


KNOWN_OPTION_ORDER = [1, 3, 6, 15, 26, 28, 51, 58, 59, 43, 114, 108, 31, 33, 40, 41, 42, 44, 46, 47, 119, 121, 249, 252, 17]


class NetworkDetector:
    def __init__(self, db_factory=SessionLocal):
        self.db_factory = db_factory
        self._monitor_threads: dict[int, threading.Thread] = {}
        self._monitor_stop_flags: dict[int, threading.Event] = {}

    def _load_known_devices(self) -> list[KnownDevice]:
        db = self.db_factory()
        try:
            devices = db.query(KnownDevice).order_by(KnownDevice.id.asc()).all()
            print(f"[detector] loaded {len(devices)} known devices from db")
            for d in devices:
                print(f"[detector] known device id={d.id} owner={d.owner_name} fp={d.dhcp_fingerprint!r}")
            return devices
        finally:
            db.close()

    def _normalize_fp(self, fp: str) -> str:
        return ",".join(str(int(part)) for part in fp.split(",") if part.strip() != "")

    def check_known_device(self, fp: str):
        normalized_fp = self._normalize_fp(fp)
        db = self.db_factory()
        try:
            device = db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == normalized_fp).first()
            print(f"[detector] lookup fp={normalized_fp!r} found={bool(device)}")
            if not device:
                for d in db.query(KnownDevice).order_by(KnownDevice.id.asc()).all():
                    print(f"[detector] candidate id={d.id} owner={d.owner_name} stored_fp={d.dhcp_fingerprint!r} normalized={self._normalize_fp(d.dhcp_fingerprint or '')!r}")
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

    def _monitor_disconnect(self, device_id: int, stop_flag: threading.Event):
        while not stop_flag.is_set():
            db = self.db_factory()
            try:
                device = db.query(KnownDevice).filter(KnownDevice.id == device_id).first()
                if not device:
                    print(f"[detector] monitor stopped device_id={device_id} not found")
                    return
                if not device.mac:
                    print(f"[detector] monitor skipped device_id={device_id} no mac")
                    return
                network = device.ip if device.ip is not None else "10.0.0.0/24"
                pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
                answered, _ = srp(pkt, timeout=2, verbose=False)
                seen = any(rcv.hwsrc == device.mac for _, rcv in answered)
                print(f"[detector] monitor device_id={device.id} owner={device.owner_name} seen={seen}")
                if not seen:
                    device_stats_service.mark_disconnected(db, device)
                    print(f"[detector] device disconnected device_id={device.id} owner={device.owner_name}")
                    return
            finally:
                db.close()
            time.sleep(random.randint(30, 60))

    def _start_monitor(self, device_id: int):
        if device_id in self._monitor_threads:
            stop_flag = self._monitor_stop_flags.get(device_id)
            if stop_flag:
                stop_flag.set()
        stop_flag = threading.Event()
        thread = threading.Thread(target=self._monitor_disconnect, args=(device_id, stop_flag), daemon=True)
        self._monitor_stop_flags[device_id] = stop_flag
        self._monitor_threads[device_id] = thread
        thread.start()
        print(f"[detector] started disconnect monitor device_id={device_id}")

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
            normalized_fp = self._normalize_fp(fp)
            device = db.query(KnownDevice).filter(KnownDevice.dhcp_fingerprint == normalized_fp).first()
            if device:
                print(f"[detector] match device_id={device.id} owner={device.owner_name}")
                device_stats_service.mark_connected(db, device, mac)
                print(f"[detector] mark_connected committed device_id={device.id} connected={device.connected} mac={device.mac}")
                self._start_monitor(device.id)
            else:
                print("[detector] no device match")
                self._load_known_devices()
        finally:
            db.close()

    def sniff_dhcp(self):
        print("[detector] sniffing dhcp on host interface")
        sniff(filter="udp and (port 67 or port 68)", prn=self.handle_dhcp_packet, store=0)


def run_detector():
    NetworkDetector().sniff_dhcp()

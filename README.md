# Device Tracker

Full-stack device tracking dashboard with FastAPI, Next.js, and SQLite.

## Overview
- **Web app** runs in Docker Compose
- **Detector service** runs on the Linux host for reliable ARP/DHCP visibility
- **SQLite** remains the storage backend
- **Login-only** access with admin-created users

## Services
- `backend`: FastAPI API + SQLite access
- `frontend`: Next.js UI
- `detector`: host-run process that listens for DHCP packets and updates device state

## Requirements
- Linux host
- Docker + Docker Compose plugin
- Python 3.11+ on the host for the detector service
- Network capture permissions for the detector (`CAP_NET_RAW` / `CAP_NET_ADMIN`)

## Default admin
- username: `admin`
- password: `admin1234`

Change this immediately after first login.

## Start the web app

1. Make sure Docker is running.
2. Start backend + frontend:
```bash
docker compose up --build
```
3. Open the app:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Run the detector on the host

The detector is designed to run outside Docker so it can see the local network traffic directly.

### Option A: Run directly with Python

1. Create a virtual environment:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the detector:
```bash
python -m app.worker
```

3. Watch the terminal output for lines like:
- `[detector] sniffing dhcp on host interface`
- `[detector] dhcp packet ...`
- `[detector] match device_id=...`

### Option B: Run as a systemd service

If you want it to start automatically on boot, create a service file like this:

```ini
[Unit]
Description=Device Tracker Detector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/Device-Tracker/backend
ExecStart=/opt/Device-Tracker/backend/.venv/bin/python -m app.worker
Restart=always
RestartSec=5
User=YOUR_LINUX_USER
Group=YOUR_LINUX_USER
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable device-tracker-detector
sudo systemctl start device-tracker-detector
sudo systemctl status device-tracker-detector
```

## Debugging / troubleshooting

### 1) Handset not detected
Most common causes:
- detector is still running in Docker instead of on the host
- the phone is on a different network/VLAN/guest Wi‑Fi
- DHCP packets were not seen because the device already had a lease and did not renew
- the fingerprint does not exactly match the stored fingerprint

Check:
- does the detector print `[detector] dhcp packet ...` lines?
- does the fingerprint in the log match one of the known devices?
- is the phone connected to the same LAN as the detector host?

### 2) Detector starts but sees nothing
- confirm the host interface is the one carrying traffic
- try reconnecting the phone to Wi‑Fi so DHCP happens again
- some routers only expose limited broadcast traffic
- ensure `CAP_NET_RAW` and `CAP_NET_ADMIN` are available

### 3) Backend startup errors
- inspect backend logs in Docker Compose
- if you see bcrypt/passlib errors, rebuild after updating dependencies
- if SQLite is locked, stop all processes using the DB and retry

### 4) Login fails
- default user is `admin / admin1234`
- if the DB volume already existed, the admin account may have been seeded earlier with a different state
- try `docker compose down -v` if you want a clean reset

### 5) Container networking questions
The detector is intentionally **not** run inside Docker because a normal container network does not reliably observe LAN DHCP/ARP traffic.
Only the web app uses Docker now; the detector should run on the host.

## Resetting to a clean state
If you want to wipe the database and start fresh:
```bash
docker compose down -v
rm -f backend/device_tracker.db
```
Then start the stack again and rerun the detector setup.

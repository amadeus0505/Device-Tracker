# Device Tracker

Full-stack device tracking dashboard with FastAPI, Next.js, and SQLite.

## Overview
- **Web app** runs in Docker Compose
- **Detector service** runs on the Linux host for reliable ARP/DHCP visibility
- **SQLite** is stored in a configurable data directory
- **Login-only** access with admin-created users

## Services
- `backend`: FastAPI API + SQLite access
- `frontend`: Next.js UI
- `detector`: host-run process that listens for DHCP packets and updates device state

## Configuration
The data directory is configured through:
```bash
DEVICE_TRACKER_DATA_DIR
```

Default:
```bash
./data
```

The SQLite database is created at:
```bash
$DEVICE_TRACKER_DATA_DIR/device_tracker.db
```

This keeps the project portable across machines while still letting the backend and detector use the same database file.

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
2. Optionally set a custom data directory:
```bash
export DEVICE_TRACKER_DATA_DIR=./data
```
3. Start backend + frontend:
```bash
docker compose up --build
```
4. Open the app:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Run the detector on the host

The detector must use the same data directory as the Docker backend.

### Option A: Run directly with Python

1. Create a virtual environment:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. If you want to grant network capabilities only to the venv Python, replace the symlink with a copy of the real binary first:
```bash
REAL_PYTHON="$(readlink -f .venv/bin/python)"
rm .venv/bin/python
cp "$REAL_PYTHON" .venv/bin/python
sudo setcap cap_net_raw+ep .venv/bin/python
sudo setcap cap_net_admin+ep .venv/bin/python
```

3. Make sure the detector points to the same data directory as Docker, for example:
```bash
export DEVICE_TRACKER_DATA_DIR=./data
```

4. Start the detector:
```bash
python -m app.worker
```

5. Watch the terminal output for lines like:
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
Environment=DEVICE_TRACKER_DATA_DIR=/opt/Device-Tracker/data
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

### 3) SQLite read-only / write errors
If you see `attempt to write a readonly database`, usually one of these is true:
- the detector is pointing at a different database file than the backend
- the `./data` directory is missing or not writable
- the backend was started before the shared `./data` mount existed
- file ownership/permissions prevent writes

Check:
```bash
mkdir -p ./data
touch ./data/device_tracker.db
ls -ld ./data
ls -l ./data/device_tracker.db
```

If needed, fix ownership:
```bash
sudo chown -R "$USER":"$USER" ./data
chmod 775 ./data
chmod 664 ./data/device_tracker.db
```

### 4) Backend startup errors
- inspect backend logs in Docker Compose
- if you see bcrypt/passlib errors, rebuild after updating dependencies
- if SQLite is locked, stop all processes using the DB and retry

### 5) Login fails
- default user is `admin / admin1234`
- if the DB already existed, the admin account may have been seeded earlier with a different state
- try `docker compose down -v` if you want a clean reset

### 6) Container networking questions
The detector is intentionally **not** run inside Docker because a normal container network does not reliably observe LAN DHCP/ARP traffic.
Only the web app uses Docker now; the detector should run on the host.

## Resetting to a clean state
If you want to wipe the database and start fresh:
```bash
docker compose down -v
rm -f ./data/device_tracker.db
```
Then start the stack again and rerun the detector setup.

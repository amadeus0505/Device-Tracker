# Device Tracker

Full-stack device tracking dashboard with FastAPI, Next.js, and SQLite.

## Features
- Login-only authentication
- Admin-created users
- Known device management
- Live connected devices dashboard
- Device history and stats
- SQLite persistence
- Background network detection abstraction

## Run locally

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker compose up --build
```

## Default admin
- username: `admin`
- password: `admin1234`

Change this immediately after first login.

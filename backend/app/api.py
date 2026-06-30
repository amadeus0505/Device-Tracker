from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.main import app as backend_app

app = FastAPI(title="Device Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("", backend_app)

"""
===========================================================
Main
-----------------------------------------------------------
FastAPI application entrypoint. Wires up CORS, creates DB
tables on startup, and includes the upload + orders routers.

Run with:
    uvicorn app.main:app --reload
Then open:
    http://127.0.0.1:8000/docs
===========================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.database_service import init_db
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.api import upload, orders, system

app = FastAPI(
    title="SmartOrder AI (OrdEasy)",
    description="Multi-agent AI order-entry backend built for the Eaton Pratibha Excellence prototype.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


@app.get("/")
def root():
    return {"status": "ok", "service": "SmartOrder AI backend is running."}


app.include_router(upload.router)
app.include_router(orders.router)
app.include_router(system.router)

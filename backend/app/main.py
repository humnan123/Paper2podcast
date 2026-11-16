import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app import models
from app.routers import auth, conferences, papers, assignments, test_auth


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Paper CMS",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


for r in (
    auth,
    conferences,
    papers,
    assignments,
    test_auth
):
    app.include_router(r.router)



@app.get("/health")
def health():
    return {
        "status": "ok"
    }
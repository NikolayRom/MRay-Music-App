from fastapi import FastAPI
from src.common.lifespan import lifespan
from src.auth.router import router as auth_router

app = FastAPI(
    title='Music Streaming App (core service)',
    lifespan=lifespan
)

app.include_router(router=auth_router)
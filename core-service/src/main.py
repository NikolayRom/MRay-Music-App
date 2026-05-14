from fastapi import FastAPI

from src.common.lifespan import lifespan

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.history.router import router as history_router

app = FastAPI(
    title='Music Streaming App (core service)',
    lifespan=lifespan
)

app.include_router(router=auth_router)
app.include_router(router=users_router)
app.include_router(router=history_router)
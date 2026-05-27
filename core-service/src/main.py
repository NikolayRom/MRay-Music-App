from fastapi import FastAPI

from src.common.lifespan import lifespan

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.history.router import router as history_router
from src.likes.router import router as likes_router
from src.playlists.router import router as playlists_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title='Music Streaming App (core service)',
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://mray-music-app.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(router=auth_router)
app.include_router(router=users_router)
app.include_router(router=history_router)
app.include_router(router=likes_router)
app.include_router(router=playlists_router)
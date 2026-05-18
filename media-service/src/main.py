from fastapi import FastAPI
from src.tracks.router import router as track_router
from src.artists.router import router as artist_router
from src.albums.router import router as album_router
from src.common.lifespan import lifespan
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title='Music Streaming App (media service)',
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"]
)

app.include_router(router=track_router)
app.include_router(router=artist_router)
app.include_router(router=album_router)
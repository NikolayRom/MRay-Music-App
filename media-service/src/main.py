from fastapi import FastAPI
from src.tracks.router import router as track_router
from src.artists.router import router as artist_router
from src.albums.router import router as album_router
from src.database import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(router=track_router)
app.include_router(router=artist_router)
app.include_router(router=album_router)
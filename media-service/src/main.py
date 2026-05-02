from fastapi import FastAPI
from src.tracks.router import router

app = FastAPI(redirect_slashes=False)

app.include_router(router=router)
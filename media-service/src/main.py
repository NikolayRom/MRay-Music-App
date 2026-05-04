from fastapi import FastAPI
from src.tracks.router import router
from src.database import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(router=router)
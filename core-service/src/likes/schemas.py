from pydantic import BaseModel
from src.models import Like
from datetime import datetime

class LikeRead(BaseModel):
    id: int
    user_id: int
    track_id: int
    created_at: datetime
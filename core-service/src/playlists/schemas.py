from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.models import Playlist

class PlaylistRead(BaseModel):
    id: int
    name: str
    user_id: int
    track_ids: List[int]
    image_key: Optional[str]
    created_at: datetime
    updated_at: datetime
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class PlaylistRead(BaseModel):
    id: int
    name: str
    user_id: int
    track_ids: List[int]
    image_key: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlaylistsAllRead(BaseModel):
    items: List[PlaylistRead]

    model_config = ConfigDict(from_attributes=True)

class PlaylistPost(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)

class PlaylistUpdate(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)

class PlaylistPatch(BaseModel):
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PlaylistTrackAdd(BaseModel):
    track_id: int

    model_config = ConfigDict(from_attributes=True)
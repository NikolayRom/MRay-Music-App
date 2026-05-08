from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.schemas.common import TrackShortRead
from src.schemas.common import AlbumShortRead

class ArtistRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    created_at: datetime

    tracks: Optional[List[TrackShortRead]] = None
    albums: Optional[List[AlbumShortRead]] = None

    model_config = ConfigDict(from_attributes=True)

class ArtistsAllRead(BaseModel):
    items: List[ArtistRead]
    has_more: bool
    next_cursor: Optional[int] = None
    limit: int

class ArtistPost(BaseModel):
    name: str

class ArtistUpdate(BaseModel):
    name: str

class ArtistPatch(BaseModel):
    name: Optional[str] = None

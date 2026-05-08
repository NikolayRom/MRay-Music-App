from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.schemas.common import TrackShortRead
from src.schemas.common import ArtistShortRead


class AlbumRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    artist_id: int
    created_at: datetime

    artist: Optional[ArtistShortRead] = None
    tracks: Optional[List[TrackShortRead]] = None

    model_config = ConfigDict(from_attributes=True)

class AlbumsAllRead(BaseModel):
    items: List[AlbumRead]
    has_more: bool
    next_cursor: Optional[int] = None
    limit: int

class AlbumPost(BaseModel):
    name: str
    artist_id: int

class AlbumUpdate(BaseModel):
    name: str
    artist_id: int

class AlbumPatch(BaseModel):
    name: Optional[str] = None
    artist_id: Optional[int] = None
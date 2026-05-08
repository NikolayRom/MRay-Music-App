from pydantic import BaseModel, ConfigDict, computed_field, Field
from pydantic.json_schema import SkipJsonSchema
from typing import List, Optional, Annotated
from datetime import datetime, timedelta
from src.schemas.common import AlbumShortRead
from src.schemas.common import ArtistShortRead

class TrackRead(BaseModel):
    id: int
    title: str
    image_key: Optional[str] = None
    genre: List[str]
    duration: Annotated[timedelta, Field(exclude=True), SkipJsonSchema()]
    created_at: datetime

    artist: Optional[ArtistShortRead] = None    
    album: Optional[AlbumShortRead] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def duration_seconds(self) -> int:
        return int(self.duration.total_seconds())

class TracksAllRead(BaseModel):
    items: List[TrackRead]
    has_more: bool
    next_cursor: Optional[int] = None
    limit: int

class TrackPost(BaseModel):
    title: Optional[str] = None
    artist_id: Optional[int] = None
    album_id: Optional[int] = None
    genre: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

class TrackUpdate(BaseModel):
    title: str
    artist_id: int
    album_id: int
    genre: List[str]

    model_config = ConfigDict(from_attributes=True)

class TrackPatch(BaseModel):
    title: Optional[str]
    artist_id: Optional[int]
    album_id: Optional[int]
    genre: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)

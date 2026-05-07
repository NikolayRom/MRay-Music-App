from pydantic import BaseModel, ConfigDict, computed_field, Field
from pydantic.json_schema import SkipJsonSchema
from typing import List, Optional, Annotated
from datetime import datetime, timedelta

class ArtistRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class AlbumRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    artist_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TrackRead(BaseModel):
    id: int
    title: str
    image_key: Optional[str] = None
    genre: List[str]
    duration: Annotated[timedelta, Field(exclude=True), SkipJsonSchema()]
    created_at: datetime

    artist: Optional[ArtistRead] = None    
    album: Optional[AlbumRead] = None

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

class TrackUpdate(BaseModel):
    title: str
    artist_id: Optional[int]
    album_id: Optional[int]
    genre: List[str]

    model_config = ConfigDict(from_attributes=True)

class TrackPatch(BaseModel):
    title: Optional[str]
    artist_id: Optional[int]
    album_id: Optional[int]
    genre: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)

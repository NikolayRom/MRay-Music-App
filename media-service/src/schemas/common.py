from pydantic import BaseModel, Field, ConfigDict, computed_field
from pydantic.json_schema import SkipJsonSchema
from typing import Optional, List, Annotated
from datetime import datetime, timedelta

class ArtistShortRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlbumShortRead(BaseModel):
    id: int
    name: str
    image_key: Optional[str] = None
    artist_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TrackShortRead(BaseModel):
    id: int
    title: str
    image_key: Optional[str] = None
    genre: List[str]
    duration: Annotated[timedelta, Field(exclude=True), SkipJsonSchema()]
    created_at: datetime

    album: Optional[AlbumShortRead]
    artist: Optional[ArtistShortRead]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def duration_seconds(self) -> int:
        return int(self.duration.total_seconds())
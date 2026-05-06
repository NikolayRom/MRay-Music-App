from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

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
    duration_seconds: int
    created_at: datetime

    artist: Optional[ArtistRead] = None    
    album: Optional[AlbumRead] = None

    model_config = ConfigDict(from_attributes=True)

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

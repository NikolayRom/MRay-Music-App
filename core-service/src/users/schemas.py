from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from src.likes.schemas import LikeRead
from src.playlists.schemas import PlaylistRead

class UserRegister(BaseModel):
    username: str
    password: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class UserAuth(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)

class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    likes: Optional[List[LikeRead]] = None
    playlists: Optional[List[PlaylistRead]] = None

    model_config = ConfigDict(from_attributes=True)
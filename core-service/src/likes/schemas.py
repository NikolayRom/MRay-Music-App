from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

class LikeRead(BaseModel):
    id: int
    user_id: int
    track_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LikesAllRead(BaseModel):
    items: List[LikeRead]

    model_config = ConfigDict(from_attributes=True)

class LikeData(BaseModel):
    track_id: int

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

class HistoryRead(BaseModel):
    id: int
    user_id: int
    track_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HistoryAllRead(BaseModel):
    items: List[HistoryRead]

    model_config = ConfigDict(from_attributes=True)

class HistoryPost(BaseModel):
    track_id: int

    model_config = ConfigDict(from_attributes=True)

class HistoryDelete(BaseModel):
    track_id: int

    model_config = ConfigDict(from_attributes=True)

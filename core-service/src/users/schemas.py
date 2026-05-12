from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

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
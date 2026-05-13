from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta, timezone
from src.config import settings

class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)

class AccessTokenCreate(BaseModel):
    sub: str
    exp: datetime

    @classmethod
    def create(cls, user_id: int, expires_minutes: int = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES) -> 'AccessTokenCreate':
        return cls(
            sub=str(user_id),
            exp=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        )

    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRead(BaseModel):
    id: int
    user_id: int
    hashed_token: str
    exp: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
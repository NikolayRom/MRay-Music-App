from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta, timezone
from src.config import settings
from typing import Optional

class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(from_attributes=True)

class AccessTokenCreate(BaseModel):
    sub: str
    is_superuser: Optional[str] = None
    exp: datetime

    @classmethod
    def create(cls, user_id: int, is_superuser: Optional[bool] = None, expires_minutes: int = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES) -> 'AccessTokenCreate':
        return cls(
            sub=str(user_id),
            is_superuser=str(is_superuser),
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

class ResetTokenRequest(BaseModel):
    token: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str
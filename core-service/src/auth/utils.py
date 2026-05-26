import hashlib
import secrets
from src.auth.schemas import AccessTokenCreate
from datetime import datetime, timedelta, timezone
import jwt
from src.config import settings
from src.models import RefreshToken, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from src.common.logger import logger
from src.common.crypt_context import CryptContext
import smtplib
from email.message import EmailMessage

pwd_context = CryptContext()

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def gen_token() -> str:
    return secrets.token_urlsafe(64)

def check_token_expired(token: RefreshToken) -> bool:
    is_expired = token.exp < datetime.now(timezone.utc)

    if is_expired:
        logger.info(f'Refresh token ({token.id}) for user ({token.user_id}) is expired')

    return is_expired

def check_token_inactive(token: RefreshToken) -> bool:
    is_inactive = not token.is_active

    if is_inactive:
        logger.info(f'Refresh token ({token.id}) for user ({token.user_id}) is inactive')

    return is_inactive

def create_access_token(user: User) -> str:
    access_token = jwt.encode(
        payload=AccessTokenCreate.create(user_id=user.id, is_superuser=user.is_superuser).model_dump(),
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    logger.info(f'Create new access token for user ({user.id})')
    return access_token

def create_refresh_token(user_id: int) -> tuple[str, RefreshToken]:
    
    refresh_token = gen_token()
    refresh_token_db = RefreshToken(
        user_id=user_id,
        hashed_token=hash_token(refresh_token),
        exp=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    logger.info(f'Create new refresh token for user ({user_id})')
    return (refresh_token, refresh_token_db)

async def clear_all_refresh_tokens(user_id: int, session: AsyncSession) -> None:
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await session.commit()
    logger.success(f'All refresh token for user ({user_id}) delete')

async def set_inactive_refresh_token(refresh_token: RefreshToken, session: AsyncSession) -> None:
    refresh_token.is_active = False
    refresh_token.exp = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(refresh_token)
    logger.info(f'Refresh token ({refresh_token.id}) for user ({refresh_token.user_id}) is inactive now')

async def get_refresh_token_from_db(token: str, session: AsyncSession) -> RefreshToken | None:
    hashed_token = hash_token(token)
    result = await session.execute(select(RefreshToken).where(RefreshToken.hashed_token == hashed_token))
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        logger.warning(f'Refresh token not found')

    return refresh_token

def send_reset_password_email(email_to: str, token: str):
    msg = EmailMessage()
    msg['Subject'] = 'Reset password - MRay music app'
    msg['From'] = settings.SMTP_USER
    msg['To'] = email_to

    reset_link = f"http://localhost:5173/reset-password?token={token}"

    msg.set_content(f"""
    To reset your password, please follow the link below:
                    
    {reset_link}

    The link is valid for 15 minutes.
    """)

    with smtplib.SMTP_SSL(host=settings.SMTP_HOST, port=settings.SMTP_PORT) as smtp:
        smtp.login(user=settings.SMTP_USER, password=settings.SMTP_PASSWORD)
        smtp.send_message(msg=msg)
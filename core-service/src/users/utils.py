from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User
from sqlalchemy import select
from src.common.logger import logger
from fastapi import UploadFile, File, HTTPException, status
from typing import List
from src.config import settings
from src.storage.client import s3_storage

async def get_user_by_username(username: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f'User with {username} username not found')

    return user

async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f'User with {email} email not found')

    return user

def get_image_key_from_file(key: str, file: UploadFile = File(...)):
    image_extension = 'jpg' if file.content_type == 'image/jpeg' else 'png'
    return f'{key}.{image_extension}'

def check_content_type_format(formats: List[str], file: UploadFile = File(...)):
    if file.content_type not in formats:
        logger.error(f'Unsupported content type format, expected {formats}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Unsupported content type format, expected {formats}')
    
def check_file_size(file: UploadFile = File(...)):
    if file.size and file.size > settings.MINIO_MAX_FILE_SIZE:
        logger.error(f'File {file.filename} size is too large: {file.size} (max: {settings.MINIO_MAX_FILE_SIZE})')
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=f'File {file.filename} is too large')
    
async def streaming_minio_data_upload(key: str, content_type: str, file: UploadFile = File(...)):
    async with s3_storage.get_client() as s3:
        logger.info(f'Streaming upload {key} key from {file.filename} to S3 storage ({s3})')
        s3_object = await s3.put_object(
            Bucket=s3_storage.bucket_name,
            Key=key,
            Body=file.file,
            ContentType=content_type
        )
        logger.success(f'Successful streamin upload for {s3_object} object from {file.filename} file')
        return s3_object
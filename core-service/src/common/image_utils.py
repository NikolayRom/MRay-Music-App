from fastapi import UploadFile, File, HTTPException, status
from src.common.logger import logger
from typing import List
from src.config import settings
from src.storage.client import s3_storage

def gen_uuid():
    return str(uuid.uuid4().hex)

async def get_image_key(key: str, file: UploadFile = File(...)) -> str:
    check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
    check_file_size(file=file)

    image_key = get_image_key_from_file(key=key, file=file)

    try:
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
        logger.success(f'Successful uploading {file.filename} with {image_key} key')
    except Exception as e:
        logger.error(f'Error, while trying to upload {file.filename} with {image_key} key: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error, while trying to upload {file.filename} with {image_key} key')

    return image_key

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
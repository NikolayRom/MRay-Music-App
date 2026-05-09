from src.config import settings
from fastapi import UploadFile, File
from src.storage.client import s3_storage
from src.common.logger import logger

def get_image_key_from_file(key: str, file: UploadFile = File(...)):
    image_extension = 'jpg' if file.content_type == 'image/jpeg' else 'png'
    return f'{settings.MINIO_COVER_ROOT}/{key}.{image_extension}'

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
    
async def default_minio_data_delete(key: str):
    async with s3_storage.get_client() as s3:
        logger.info(f'Trying to delete object with {key} key from S3 storage ({s3})')
        await s3.delete_object(
            Bucket=s3_storage.bucket_name,
            Key=key,
        )
        logger.success(f'Successful delete object with {key} key from S3 storage')
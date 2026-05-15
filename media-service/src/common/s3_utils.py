from src.config import settings
from fastapi import UploadFile, File
from src.storage.client import s3_storage, s3_assets_policy, s3_assets_storage
from src.common.logger import logger
import json

def get_image_key_from_file(key: str, file: UploadFile = File(...)):
    image_extension = 'jpg' if file.content_type == 'image/jpeg' else 'png'
    return f'{key}.{image_extension}'

async def streaming_minio_data_upload(key: str, content_type: str, file: UploadFile = File(...), is_public: bool = False):
    if is_public:
        bucket_name = s3_assets_storage.bucket_name
    else:
        bucket_name = s3_storage.bucket_name

    async with s3_storage.get_client() as s3:
        logger.info(f'Streaming upload {key} key from {file.filename} to S3 storage ({s3})')
        s3_object = await s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=file.file,
            ContentType=content_type
        )
        logger.success(f'Successful streamin upload for {s3_object} object from {file.filename} file')
        return s3_object
    
async def default_minio_data_delete(key: str, is_public: bool = False):
    if is_public:
        bucket_name = s3_assets_storage.bucket_name
    else:
        bucket_name = s3_storage.bucket_name

    
    async with s3_storage.get_client() as s3:
        logger.info(f'Trying to delete object with {key} key from S3 storage ({s3})')
        await s3.delete_object(
            Bucket=bucket_name,
            Key=key,
        )
        logger.success(f'Successful delete object with {key} key from S3 storage')

async def set_public_bucket_policy(bucket_name: str):
    async with s3_assets_policy.get_client() as s3:
        try:
            await s3.head_bucket(Bucket=bucket_name)
        except:
            await s3.create_bucket(Bucket=bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
        
        policy = {
            'Version': "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }

        await s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(policy)
        )
    logger.info(f'Set PUBLIC policy for {bucket_name} bucket in MinIO')
import aioboto3
from src.config import settings
from src.common.logger import logger

class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.url = settings.MINIO_URL
        self.access_key = settings.MINIO_ROOT_USER
        self.secret_key = settings.MINIO_ROOT_PASSWORD
        self.bucket_name = settings.MINIO_BUCKET_NAME_CORE

    def get_client(self):
        logger.info(f'Get S3 client session {self.session}')
        return self.session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

s3_storage = S3Client()
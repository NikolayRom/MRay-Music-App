import aioboto3
from src.config import settings

class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.url = settings.MINIO_URL
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_NAME

    def get_client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

s3_storage = S3Client()
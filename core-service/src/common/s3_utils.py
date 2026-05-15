import json
from src.storage.client import s3_policy
from src.common.logger import logger

async def set_public_bucket_policy(bucket_name: str):
    async with s3_policy.get_client() as s3:
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

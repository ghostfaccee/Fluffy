from contextlib import AbstractAsyncContextManager

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from aiobotocore.client import AioBaseClient

from app.core import env_settings, yaml_settings, logger

class S3Service:
    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.bucket = env_settings.S3_AVATARS_BUCKET_NAME
        self.endpoint_url = env_settings.S3_AVATARS_ENDPOINT_URL
        self.region = env_settings.S3_AVATARS_REGION
        self.access_key = env_settings.S3_AVATARS_ACCESS_KEY
        self.secret_key = env_settings.S3_AVATARS_SECRET_KEY
    
    def _get_client(self) -> AbstractAsyncContextManager[AioBaseClient]:
        return self.session.client(
            's3',
            endpoint_url = self.endpoint_url,
            region_name = self.region,
            aws_access_key_id = self.access_key,
            aws_secret_access_key = self.secret_key,
            config = Config(signature_version = 's3v4')
        )
    
    async def generate_presigned_put_url(
        self, 
        key: str, 
        content_type: str, 
        expires_in: int = yaml_settings.AVATAR_PRESIGNED_PUT_URL_LIFETIME_MINUTES * 60
    ) -> str:
        async with self._get_client() as s3:
            url: str = await s3.generate_presigned_url(
                ClientMethod = 'put_object',
                Params = {
                    'Bucket' : self.bucket,
                    'Key' : key,
                    'ContentType' : content_type
                },
                ExpiresIn = expires_in
            )
            return url
    
    async def generate_presigned_get_url(
        self,
        key: str,
        expires_in: int = yaml_settings.AVATAR_PRESIGNED_GET_URL_LIFETIME_MINUTES * 60
    ) -> str:
        async with self._get_client() as s3:
            url: str = await s3.generate_presigned_url(
                ClientMethod = 'get_object',
                Params = {
                    'Bucket' : self.bucket,
                    'Key' : key
                },
                ExpiresIn = expires_in
            )
            return url
    
    async def delete_object(self, key: str) -> bool:
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket = self.bucket, Key = key)
            return True
        except ClientError as e:
            logger.error(f'Failed to delete S3 object: {key}: {e}')
            return False

s3_avatars: S3Service = S3Service()

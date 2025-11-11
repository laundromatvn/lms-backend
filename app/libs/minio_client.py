import io
import minio
from minio.datatypes import Object
from datetime import timedelta
from typing import BinaryIO, Union

from app.core.config import settings


class MinioClient:
    def __init__(
        self,
        endpoint: str = settings.MINIO_ENDPOINT,
        access_key: str = settings.MINIO_ACCESS_KEY,
        secret_key: str = settings.MINIO_SECRET_KEY,
        secure: bool = settings.MINIO_SECURE,
    ):
        self.minio_client = minio.Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        
    def upload_file(self, bucket_name: str, object_name: str, data: Union[BinaryIO, bytes]) -> None:
        """Upload file bytes to MinIO."""
        # If data is bytes, wrap it in BytesIO
        if isinstance(data, bytes):
            data = io.BytesIO(data)
        
        # Get the length of the data
        data.seek(0, io.SEEK_END)
        length = data.tell()
        data.seek(0)
        
        self.minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data,
            length=length,
        )

    def get_file_metadata(self, bucket_name: str, object_name: str) -> Object:
        return self.minio_client.stat_object(
            bucket_name=bucket_name,
            object_name=object_name,
        )
        
    def get_file_url(self, bucket_name: str, object_name: str, expires: timedelta = timedelta(days=1)) -> str:
        return self.minio_client.get_presigned_url(
            'GET',
            bucket_name=bucket_name,
            object_name=object_name,
            expires=expires,
        )
        
    def get_permanent_file_url(self, bucket_name: str, object_name: str) -> str:
        return self.minio_client.get_presigned_url(
            'GET',
            bucket_name=bucket_name,
            object_name=object_name,
            expires=None,
        )

    def get_public_file_url(self, object_name: str) -> str:
        return f"{settings.MINIO_URL}/{object_name}"



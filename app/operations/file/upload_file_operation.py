from datetime import datetime, timedelta
import random
import string

from fastapi import UploadFile

from app.core.config import settings
from app.libs.minio_client import MinioClient


class UploadFileOperation:
    
    FIRMWARE_PATH = "firmware"
    
    def __init__(self, file_name: str):
        self.minio_client = MinioClient()
        self.object_name = self._generate_object_name(file_name)

    def execute(self, chunk: bytes):
        try:
            self.minio_client.upload_file(
                bucket_name=settings.BUCKET_NAME,
                object_name=self.object_name,
                data=chunk,
            )

            self.result = self._get_file_metadata()
        except Exception as e:
            raise ValueError(f"Failed to upload file: {e}")

    def _generate_object_name(self, filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        object_name = f"{settings.PUBLIC_FOLDER_PATH}/{self.FIRMWARE_PATH}/{timestamp}_{random_string}_{filename}"
        return object_name

    def _get_file_metadata(self) -> dict:
        return self.minio_client.get_file_metadata(
            bucket_name=settings.BUCKET_NAME,
            object_name=self.object_name,
        )

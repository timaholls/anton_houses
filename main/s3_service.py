import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config
import boto3

# Загружаем .env из корня проекта
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=".env")


class S3Service:
    """
    Обертка над boto3 для загрузки изображений в S3-совместимое хранилище.
    Ожидает следующие ENV переменные:
      - AWS_S3_ENDPOINT_URL
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
      - AWS_S3_REGION_NAME
      - AWS_STORAGE_BUCKET_NAME
    """

    def __init__(self):
        endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
        self.bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
        AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

        # S3 access credentials
        AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

        # S3 endpoint for TimeWeb Cloud
        AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', 'https://s3.timeweb.cloud')

        # S3 region
        AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ru-1')

        self.s3_client = boto3.client(
            's3',
            endpoint_url=AWS_S3_ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME,
            use_ssl=False,
        )
        self.bucket_name = AWS_STORAGE_BUCKET_NAME

        self.public_base = f"{endpoint_url}/{self.bucket_name}"

    def build_url(self, key: str) -> str:
        """Формирует публичный URL для доступа к файлу в S3."""
        key = key.lstrip("/")
        return f"{self.public_base}/{key}"

    def upload_bytes(self, data: bytes, key: str, content_type: Optional[str] = "image/jpeg") -> str:
        """Загружает байты в S3 по ключу и возвращает публичный URL."""
        key = key.lstrip("/")

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        
        # Формируем URL как s3_url = f"https://s3.timeweb.cloud/{bucket}/{key}"
        return self.build_url(key)

    def upload_fileobj(self, file_obj, key: str, content_type: Optional[str] = None) -> str:
        """Загружает файловый объект в S3 и возвращает публичный URL."""
        key = key.lstrip("/")
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket_name,
            key,
            ExtraArgs=extra_args if extra_args else None
        )
        
        return self.build_url(key)

    def delete_object(self, key: str) -> None:
        """Удаляет объект из S3 по ключу."""
        key = key.lstrip("/")
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except Exception as e:
            pass

    def delete_prefix(self, prefix: str) -> None:
        """Удаляет все объекты с указанным префиксом."""
        prefix = prefix.lstrip("/")
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                if objects:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': objects}
                    )
        except Exception as e:
            pass

    def exists(self, key: str) -> bool:
        """Проверяет существование объекта в S3."""
        key = key.lstrip("/")
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False

    def list_objects(self, prefix: str) -> list:
        """Возвращает список ключей объектов с указанным префиксом."""
        prefix = prefix.lstrip("/")
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            return []

    def extract_key_from_url(self, url: str) -> str:
        """Извлекает ключ S3 из полного URL."""
        if not url:
            return ""
        # Убираем базовый URL
        if self.public_base in url:
            return url.replace(self.public_base + "/", "")
        # Если URL начинается с другого домена, пытаемся найти bucket_name
        if self.bucket_name in url:
            parts = url.split(self.bucket_name + "/")
            if len(parts) > 1:
                return parts[1]
        return url


# Создаем глобальный экземпляр для использования в приложении
s3_client = S3Service()

# Константа для плейсхолдера (можно загрузить в S3 или использовать CDN)
PLACEHOLDER_IMAGE_URL = f"{s3_client.public_base}/gallery/placeholders.png"

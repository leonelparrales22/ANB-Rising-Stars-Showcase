import os
import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional
from shared.config.settings import settings


class StorageBackend:
    """Interfaz base"""

    def upload_file(self, file_path: str, key: str) -> str:
        """Sube un archivo y retorna la URL"""
        raise NotImplementedError

    def upload_fileobj(self, file_obj: BinaryIO, key: str) -> str:
        """Sube un objeto de archivo y retorna la URL"""
        raise NotImplementedError

    def download_file(self, key: str, local_path: str) -> None:
        """Descarga un archivo a ruta local"""
        raise NotImplementedError

    def delete_file(self, key: str) -> bool:
        """Elimina un archivo"""
        raise NotImplementedError

    def file_exists(self, key: str) -> bool:
        """Verifica si un archivo existe"""
        raise NotImplementedError

    def get_file_url(self, key: str) -> str:
        """Retorna la URL pública del archivo"""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Backend de almacenamiento local"""

    def __init__(self, base_dir: str = settings.uploads_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_path: str, key: str) -> str:
        """Copia archivo local a local"""
        dest_path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
            dst.write(src.read())

        return dest_path

    def upload_fileobj(self, file_obj: BinaryIO, key: str) -> str:
        """Guarda objeto de archivo localmente"""
        dest_path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "wb") as f:
            f.write(file_obj.read())

        return dest_path

    def download_file(self, key: str, local_path: str) -> None:
        """Copia archivo local a local"""
        src_path = os.path.join(self.base_dir, key)
        with open(src_path, "rb") as src, open(local_path, "wb") as dst:
            dst.write(src.read())

    def delete_file(self, key: str) -> bool:
        """Elimina archivo local"""
        file_path = os.path.join(self.base_dir, key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def file_exists(self, key: str) -> bool:
        """Verifica si archivo existe localmente"""
        return os.path.exists(os.path.join(self.base_dir, key))

    def get_file_url(self, key: str) -> str:
        """Retorna ruta local como URL"""
        return os.path.join(self.base_dir, key)


class S3Storage(StorageBackend):
    """Backend de almacenamiento AWS S3"""

    def __init__(self, bucket_name: str = settings.s3_bucket):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token,
            region_name=settings.aws_region,
        )

    def upload_file(self, file_path: str, key: str) -> str:
        """Sube archivo a S3"""
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, key)
            return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"
        except ClientError as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    def upload_fileobj(self, file_obj: BinaryIO, key: str) -> str:
        """Sube objeto de archivo a S3"""
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, key)
            return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"
        except ClientError as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    def download_file(self, key: str, local_path: str) -> None:
        """Descarga archivo desde S3"""
        try:
            self.s3_client.download_file(self.bucket_name, key, local_path)
        except ClientError as e:
            raise Exception(f"Error downloading from S3: {str(e)}")

    def delete_file(self, key: str) -> bool:
        """Elimina archivo de S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def file_exists(self, key: str) -> bool:
        """Verifica si archivo existe en S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def get_file_url(self, key: str) -> str:
        """Retorna URL de S3"""
        return (
            f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"
        )


class StorageManager:
    """Gestor de almacenamiento que decide qué backend usar"""

    def __init__(self):
        # Determinar backend basado en configuración
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.backend = S3Storage()
            self.storage_type = "s3"
        else:
            self.backend = LocalStorage()
            self.storage_type = "local"

    def upload_video(self, file_obj: BinaryIO, video_id: str, filename: str) -> str:
        """Sube un video y retorna la URL"""
        key = f"videos/{video_id}/{filename}"
        return self.backend.upload_fileobj(file_obj, key)

    def upload_processed_video(self, local_path: str, video_id: str) -> str:
        """Sube un video procesado"""
        key = f"processed/{video_id}/processed_{video_id}.mp4"
        return self.backend.upload_file(local_path, key)

    def download_video(self, video_url: str, local_path: str) -> None:
        """Descarga un video para procesamiento"""
        if self.storage_type == "s3":
            # Extraer key de la URL de S3
            key = video_url.split(".amazonaws.com/")[-1]
            self.backend.download_file(key, local_path)
        else:
            # Para local, solo copiar
            with open(video_url, "rb") as src, open(local_path, "wb") as dst:
                dst.write(src.read())

    def delete_video(self, video_url: str) -> bool:
        """Elimina un video"""
        if self.storage_type == "s3":
            key = video_url.split(".amazonaws.com/")[-1]
            return self.backend.delete_file(key)
        else:
            if os.path.exists(video_url):
                os.remove(video_url)
                return True
            return False

    def get_video_url(self, video_id: str, filename: str) -> str:
        """Genera URL para un video"""
        key = f"videos/{video_id}/{filename}"
        return self.backend.get_file_url(key)

    def get_processed_video_url(self, video_id: str) -> str:
        """Genera URL para video procesado"""
        key = f"processed/{video_id}/processed_{video_id}.mp4"
        return self.backend.get_file_url(key)

# Instancia global
storage_manager = StorageManager()

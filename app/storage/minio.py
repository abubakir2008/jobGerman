from minio import Minio
from minio import S3Error

from app.config.config import settings

minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL,
)


def ensure_bucket_exists() -> None:
    try:
        if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    except S3Error as e:
        raise RuntimeError(f"MinIO bucket error: {e}")


def upload_file(file_data: bytes, object_name: str, content_type: str) -> str:
    import io

    minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{object_name}"


def delete_file(object_name: str) -> None:
    minio_client.remove_object(settings.MINIO_BUCKET_NAME, object_name)
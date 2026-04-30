from datetime import timedelta

from minio import Minio
from minio import S3Error

from app.config.config import settings

# Внутренний клиент — общается с MinIO по docker-сети ("minio:9000")
minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL,
)

# Публичный endpoint — то, что доступно из браузера (через docker port-forward).
PUBLIC_ENDPOINT = settings.MINIO_PUBLIC_ENDPOINT or "localhost:9000"

# Клиент-«синтезатор» presigned URL: подписывает запросы для публичного хоста.
# `presigned_get_object` не делает сетевых вызовов — только crypto, поэтому
# тот факт, что localhost:9000 недоступен изнутри контейнера, не мешает.
public_signer = Minio(
    endpoint=PUBLIC_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL,
    # Явно задаём region — иначе minio-py попытается сходить по сети
    # за `?location=` и упадёт, т.к. localhost:9000 из контейнера недоступен.
    region="us-east-1",
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


def extract_object_name(file_url: str) -> str:
    """Из «http://minio:9000/germany-jobs/path/to/file.pdf» достаём object_name."""
    bucket = settings.MINIO_BUCKET_NAME
    marker = f"/{bucket}/"
    if marker in file_url:
        return file_url.split(marker, 1)[1]
    from urllib.parse import urlparse
    path = urlparse(file_url).path.lstrip("/")
    if path.startswith(f"{bucket}/"):
        return path[len(bucket) + 1:]
    return path


def get_presigned_url(object_name: str, expires_minutes: int = 60) -> str:
    """Сгенерировать временный URL, доступный из браузера.

    Подпись делается под `PUBLIC_ENDPOINT`, чтобы host header в подписи
    совпадал с реальным хостом, к которому будет обращаться браузер.
    """
    return public_signer.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(minutes=expires_minutes),
    )


def get_presigned_url_from_file_url(file_url: str, expires_minutes: int = 60) -> str:
    """Принимает сохранённый file_url, отдаёт presigned URL для просмотра."""
    return get_presigned_url(extract_object_name(file_url), expires_minutes)

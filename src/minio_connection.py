from minio import Minio
from minio.error import S3Error
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl


class MinioSettings(BaseSettings):
    minio_endpoint: str = Field(default="0.0.0.0:9010", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(alias="MINIO_ROOT_PASSWORD")
    bucket_name: str = Field(default="logging", alias="MINIO_BUCKET")


minio_settings = MinioSettings()

client = Minio(
    endpoint=minio_settings.minio_endpoint,
    access_key=minio_settings.minio_access_key,
    secret_key=minio_settings.minio_secret_key,
    secure=False,
)


def save_log(source_file: str):

    # The destination bucket and filename on the MinIO server
    bucket_name = minio_settings.bucket_name

    # Make the bucket if it doesn't exist.
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)

    # Upload the file, renaming it in the process
    client.fput_object(
        minio_settings.bucket_name,
        source_file,
        source_file,
    )

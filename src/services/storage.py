"""
MinIO storage service for file operations.
"""
import io
import logging
from typing import Optional
from uuid import uuid4

import minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO storage service for document files."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str = "docops",
        secure: bool = False
    ):
        """Initialize MinIO client."""
        self.client = minio.Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        folder: str = "raw"
    ) -> str:
        """
        Upload a file to MinIO.

        Returns the MinIO key (path) of the uploaded file.
        """
        # Generate unique key
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        key = f"{folder}/{uuid4()}.{ext}" if ext else f"{folder}/{uuid4()}"

        try:
            self.client.put_object(
                self.bucket,
                key,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return key
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")

    def download_file(self, key: str) -> bytes:
        """
        Download a file from MinIO.
        """
        try:
            response = self.client.get_object(self.bucket, key)
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")
        finally:
            response.close()
            response.release_conn()

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from MinIO.
        """
        try:
            self.client.remove_object(self.bucket, key)
            return True
        except S3Error as e:
            raise Exception(f"Failed to delete file: {e}")

    def get_file_url(self, key: str, expires: int = 3600) -> str:
        """
        Get a presigned URL for a file.
        """
        try:
            return self.client.presigned_get_object(self.bucket, key, expires)
        except S3Error as e:
            raise Exception(f"Failed to generate URL: {e}")

    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in the bucket with optional prefix.
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise Exception(f"Failed to list files: {e}")

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in the bucket.
        """
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except S3Error:
            return False

    def copy_file(self, source_key: str, destination_key: str) -> str:
        """
        Copy a file within the bucket.
        """
        try:
            self.client.copy_object(
                self.bucket,
                destination_key,
                f"{self.bucket}/{source_key}"
            )
            return destination_key
        except S3Error as e:
            raise Exception(f"Failed to copy file: {e}")

    def get_bucket_policy(self) -> Optional[dict]:
        """
        Get bucket policy.
        """
        try:
            policy = self.client.get_bucket_policy(self.bucket)
            return policy
        except S3Error:
            return None

    def set_bucket_policy(self, policy: dict):
        """
        Set bucket policy.
        """
        try:
            self.client.set_bucket_policy(self.bucket, policy)
        except S3Error as e:
            raise Exception(f"Failed to set bucket policy: {e}")


def get_default_bucket_policy(bucket_name: str) -> dict:
    """
    Get the default bucket policy for the docops bucket.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            },
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            },
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:DeleteObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            }
        ]
    }

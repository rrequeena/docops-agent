"""
Shared FastAPI dependencies.
"""
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    """
    # TODO: Implement actual database session
    # This will be implemented with SQLAlchemy
    pass


async def get_redis():
    """
    Redis client dependency.
    """
    # TODO: Implement actual Redis client
    pass


async def get_minio():
    """
    MinIO client dependency.
    """
    # TODO: Implement actual MinIO client
    pass

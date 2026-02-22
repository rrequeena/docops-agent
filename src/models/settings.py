"""
Settings model for storing application settings in database.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.models.document import Base


class AppSettings(Base):
    """Application settings stored in database."""
    __tablename__ = "app_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(String(512), nullable=False)
    value_type = Column(String(32), default="string")  # string, int, float, bool
    description = Column(String(256))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AppSettings(key={self.key}, value={self.value})>"

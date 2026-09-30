"""
DecrypTrace — ORM Models: Document
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


class Document(Base):
    """A document uploaded and encrypted for secure distribution."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="v1")
    document_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="SHA3-256 hash of original plaintext"
    )
    encrypted_path: Mapped[str] = mapped_column(
        Text, nullable=True, comment="Path to encrypted file on disk"
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    encryption_algorithm: Mapped[str] = mapped_column(
        String(50), default="AES-256-GCM"
    )
    kem_algorithm: Mapped[str] = mapped_column(
        String(50), default="ML-KEM-768"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="uploaded",
        comment="uploaded | encrypted | distributed"
    )
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    from sqlalchemy import JSON
    envelopes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

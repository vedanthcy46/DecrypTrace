"""
DecrypTrace — ORM Models: Forensic Record

Results of investigating a leaked document.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


class ForensicReport(Base):
    """Result of a forensic investigation on a leaked document."""

    __tablename__ = "forensic_reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False,
        comment="Human-readable report ID e.g. FR-20260930-001"
    )

    # Source
    leaked_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    leaked_file_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    # Watermark extraction
    watermark_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_watermark_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    watermark_integrity_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Ledger match
    ledger_match: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    matched_block_index: Mapped[int | None] = mapped_column(nullable=True)

    # Signature verification
    signature_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    document_hash_match: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Attribution result
    attributed_recipient_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    attributed_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attribution_status: Mapped[str] = mapped_column(
        String(30), default="pending",
        comment="pending | confirmed | not_found | integrity_fail | signature_fail"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

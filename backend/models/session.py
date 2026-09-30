"""
DecrypTrace — ORM Models: Decryption Session

Tracks the multi-step decryption workflow:
  prepare → session created → evidence submitted → committed to DLT
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


class DecryptionSession(Base):
    """A decryption event session linking document, recipient, and watermark."""

    __tablename__ = "decryption_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        comment="Human-readable session ID e.g. SES-93F1"
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Watermark binding
    watermark_id: Mapped[str] = mapped_column(
        String(50), nullable=True,
        comment="Pseudonymous watermark ID e.g. WM-7A92"
    )
    watermark_algorithm: Mapped[str] = mapped_column(
        String(50), default="DCT-BLIND-128"
    )

    # Cryptographic evidence
    recipient_signature: Mapped[str] = mapped_column(
        Text, nullable=True,
        comment="ML-DSA signature over canonical decryption record"
    )
    signature_algorithm: Mapped[str] = mapped_column(
        String(50), default="ML-DSA-65"
    )
    canonical_record_hash: Mapped[str] = mapped_column(
        String(128), nullable=True,
        comment="SHA3-256 of the canonical decryption record"
    )

    # DLT binding
    ledger_block_index: Mapped[int | None] = mapped_column(nullable=True)
    ledger_committed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(30), default="prepared",
        comment="prepared | evidence_submitted | committed | failed"
    )
    client_instance_id: Mapped[str] = mapped_column(
        String(50), nullable=True,
        comment="Identifier of the recipient's local agent instance"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    committed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

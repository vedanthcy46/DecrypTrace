"""
DecrypTrace — ORM Models: Recipient

IMPORTANT: This model stores PUBLIC keys only.
Private keys are generated and stored exclusively on the recipient's device.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


class Recipient(Base):
    """A registered document recipient. Only PUBLIC keys are stored here."""

    __tablename__ = "recipients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    callsign: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        comment="Short identifier e.g. ALPHA, BRAVO, CHARLIE"
    )
    email: Mapped[str] = mapped_column(String(255), nullable=True)

    # PUBLIC keys only — private keys are on the recipient device
    ml_kem_public_key: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="ML-KEM-768 public key (base64 encoded)"
    )
    ml_dsa_public_key: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="ML-DSA-65 public key (base64 encoded)"
    )
    key_fingerprint: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="SHA3-256 fingerprint of ML-DSA public key"
    )

    status: Mapped[str] = mapped_column(
        String(20), default="active",
        comment="active | suspended | revoked"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

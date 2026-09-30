"""
DecrypTrace — Pydantic Schemas

Request/response models for the API.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ── Documents ──

class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    document_hash: str
    file_size: int
    page_count: int
    status: str
    created_at: datetime


class DocumentEncryptRequest(BaseModel):
    recipient_ids: list[str] = Field(
        ..., description="List of recipient IDs to encrypt for"
    )


class DocumentEncryptResponse(BaseModel):
    document_id: str
    status: str
    recipient_count: int
    envelopes: list[dict]  # Per-recipient KEM ciphertext info


class DocumentListItem(BaseModel):
    id: str
    title: str
    version: str
    status: str
    recipient_count: int
    encryption_algorithm: str
    created_at: datetime


# ── Recipients ──

class RecipientRegisterRequest(BaseModel):
    """
    Registration payload. Contains PUBLIC keys only.
    Private keys are generated on the recipient device.
    """
    name: str
    callsign: str = Field(
        ..., description="Short identifier e.g. ALPHA, BRAVO"
    )
    email: Optional[str] = None
    ml_kem_public_key: str = Field(
        ..., description="ML-KEM-768 public key (base64)"
    )
    ml_dsa_public_key: str = Field(
        ..., description="ML-DSA-65 public key (base64)"
    )


class RecipientResponse(BaseModel):
    id: str
    name: str
    callsign: str
    email: Optional[str]
    key_fingerprint: str
    status: str
    created_at: datetime


# ── Decryption Sessions ──

class PrepareDecryptionResponse(BaseModel):
    """Data needed by the recipient agent to decrypt."""
    session_id: str
    document_id: str
    encrypted_document_b64: str  # Base64 encoded encrypted content
    kem_ciphertext_b64: str      # ML-KEM ciphertext for this recipient
    wrapped_dek_b64: str         # AES key wrapped with KEK
    kek_nonce_b64: str           # Nonce used to wrap DEK
    nonce_b64: str               # AES-GCM nonce
    document_hash: str           # For verification after decryption
    watermark_id: str            # Assigned watermark ID


class SubmitEvidenceRequest(BaseModel):
    """Signed decryption record from the recipient agent."""
    canonical_record: dict = Field(
        ..., description="The canonical decryption record (JSON)"
    )
    recipient_signature: str = Field(
        ..., description="ML-DSA signature over canonical record (base64)"
    )
    signature_algorithm: str = "ML-DSA-65"
    client_instance_id: Optional[str] = None


class DecryptionSessionResponse(BaseModel):
    session_id: str
    document_id: str
    recipient_id: str
    watermark_id: Optional[str]
    status: str
    ledger_committed: bool
    ledger_block_index: Optional[int]
    created_at: datetime


# ── Forensics ──

class ForensicAnalysisResponse(BaseModel):
    report_id: str
    watermark_detected: bool
    extracted_watermark_id: Optional[str]
    watermark_integrity_valid: Optional[bool]
    ledger_match: bool
    matched_session_id: Optional[str]
    matched_block_index: Optional[int]
    signature_verified: Optional[bool]
    document_hash_match: Optional[bool]
    attributed_recipient_id: Optional[str]
    attributed_recipient_callsign: Optional[str]
    attributed_key_fingerprint: Optional[str]
    attribution_status: str
    created_at: datetime


# ── Ledger ──

class LedgerBlockResponse(BaseModel):
    index: int
    timestamp: str
    transactions: list[dict]
    previous_hash: str
    hash: str
    endorsements: list[dict]


class LedgerHealthResponse(BaseModel):
    nodes: list[dict]
    chain_length: int
    integrity_verified: bool


class TamperTestResponse(BaseModel):
    tamper_type: str
    node_targeted: str
    divergence_detected: bool
    details: str

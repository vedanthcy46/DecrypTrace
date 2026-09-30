"""
DecrypTrace — Recipient Agent Routes

Handles all recipient-side operations:
  1. Key generation (local)
  2. Decryption (ML-KEM decapsulate + AES-GCM decrypt)
  3. Watermark embedding
  4. Record creation + ML-DSA signing
  5. Submit signed evidence to backend
"""
import os
import json
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from crypto.keystore import (
    generate_keypair, load_keypair, list_keypairs, RecipientKeyPair,
)

logger = logging.getLogger("recipient-agent.routes")
router = APIRouter()

# Watermark secret (shared with backend for validation)
WATERMARK_SECRET = b"decryptrace-watermark-secret-change-in-production"


# ── Request/Response Models ──

class GenerateKeysRequest(BaseModel):
    callsign: str = Field(..., description="Recipient callsign e.g. ALPHA")
    name: str = Field(default="", description="Display name")


class GenerateKeysResponse(BaseModel):
    recipient_id: str
    callsign: str
    kem_public_key: str  # base64
    dsa_public_key: str  # base64
    key_fingerprint: str
    message: str


class DecryptRequest(BaseModel):
    """Data from the backend's prepare-decryption endpoint."""
    session_id: str
    document_id: str
    encrypted_document_b64: str
    kem_ciphertext_b64: str
    wrapped_dek_b64: str
    kek_nonce_b64: str
    nonce_b64: str
    document_hash: str
    watermark_id: str
    callsign: str


class DecryptResponse(BaseModel):
    session_id: str
    document_id: str
    watermark_id: str
    canonical_record: dict
    recipient_signature: str  # base64
    signature_algorithm: str
    decrypted_document_b64: str
    success: bool
    message: str


# ── Endpoints ──

@router.post("/keys/generate", response_model=GenerateKeysResponse)
async def generate_keys(req: GenerateKeysRequest):
    """
    Generate ML-KEM + ML-DSA key pairs LOCALLY.
    Private keys never leave this device.
    Returns only public keys for registration with the backend.

    IMPORTANT: If keys already exist for this callsign, the EXISTING keys
    are returned — not new ones. This prevents key rotation breaking
    decryption of documents encrypted with the old public key.
    To force new keys, the recipient must explicitly rotate (future feature).
    """
    # Check if keys already exist for this callsign
    existing = load_keypair(req.callsign)
    if existing:
        logger.info(f"Keys already exist for {req.callsign} — returning existing keys")
        return GenerateKeysResponse(
            recipient_id=existing.recipient_id,
            callsign=existing.callsign,
            kem_public_key=base64.b64encode(existing.kem_public_key).decode(),
            dsa_public_key=base64.b64encode(existing.dsa_public_key).decode(),
            key_fingerprint=existing.key_fingerprint,
            message=f"Existing keys loaded for {req.callsign}. Private keys are on this device.",
        )

    # No existing keys — generate fresh
    import uuid
    recipient_id = str(uuid.uuid4())
    keypair = generate_keypair(recipient_id, req.callsign)
    logger.info(f"New keys generated for {req.callsign}")

    return GenerateKeysResponse(
        recipient_id=recipient_id,
        callsign=req.callsign,
        kem_public_key=base64.b64encode(keypair.kem_public_key).decode(),
        dsa_public_key=base64.b64encode(keypair.dsa_public_key).decode(),
        key_fingerprint=keypair.key_fingerprint,
        message=f"Keys generated locally for {req.callsign}. Private keys stored on device.",
    )


@router.get("/keys")
async def list_keys():
    """List locally stored key pairs (public info only)."""
    return {"keypairs": list_keypairs()}

@router.get("/keys/list")
async def list_keys_alias():
    """Alias for /keys."""
    return {"keypairs": list_keypairs()}




@router.post("/keys/rotate", response_model=GenerateKeysResponse)
async def rotate_keys(req: GenerateKeysRequest):
    """
    Explicitly rotate keys for a callsign.
    WARNING: Old documents encrypted with the previous public key will
    no longer be decryptable after rotation. Re-encrypt them on the Sender side.
    """
    import uuid
    recipient_id = str(uuid.uuid4())
    keypair = generate_keypair(recipient_id, req.callsign)
    logger.warning(f"Keys ROTATED for {req.callsign} — old encrypted documents are now inaccessible")
    return GenerateKeysResponse(
        recipient_id=recipient_id,
        callsign=req.callsign,
        kem_public_key=base64.b64encode(keypair.kem_public_key).decode(),
        dsa_public_key=base64.b64encode(keypair.dsa_public_key).decode(),
        key_fingerprint=keypair.key_fingerprint,
        message=f"Keys ROTATED for {req.callsign}. Old documents can no longer be decrypted.",
    )

@router.post("/decrypt", response_model=DecryptResponse)
async def decrypt_document(req: DecryptRequest):
    """
    Full decryption pipeline (runs entirely on recipient device):
    1. Load local private keys
    2. ML-KEM decapsulate → recover AES key
    3. AES-GCM decrypt document
    4. Generate watermark payload with integrity tag
    5. Create canonical decryption record
    6. Sign record with local ML-DSA private key
    7. Return signed evidence + decrypted document
    """
    # 1. Load local keys
    keypair = load_keypair(req.callsign)
    if not keypair:
        raise HTTPException(404, f"No keys found for {req.callsign}. Generate keys first.")

    # 2. ML-KEM decapsulate (simulated with X25519)
    try:
        kem_ciphertext = base64.b64decode(req.kem_ciphertext_b64)
        kem_private = x25519.X25519PrivateKey.from_private_bytes(keypair.kem_private_key)
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(kem_ciphertext)
        shared_key = kem_private.exchange(ephemeral_pub)

        # Derive Key Encryption Key (KEK)
        kek = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"simulation_kem",
        ).derive(shared_key)
        
        # Unwrap the DEK
        kek_nonce = base64.b64decode(req.kek_nonce_b64)
        wrapped_dek = base64.b64decode(req.wrapped_dek_b64)
        kek_gcm = AESGCM(kek)
        aes_key = kek_gcm.decrypt(kek_nonce, wrapped_dek, None)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(400, f"ML-KEM decapsulation failed: {e}")

    # 3. AES-GCM decrypt
    try:
        nonce = base64.b64decode(req.nonce_b64)
        # The encrypted file contains [12-byte nonce][ciphertext]
        # We extract just the ciphertext for the decrypt() call
        encrypted_doc = base64.b64decode(req.encrypted_document_b64)[12:]
        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, encrypted_doc, None)
    except Exception as e:
        raise HTTPException(400, f"AES-GCM decryption failed: {e}")

    # Verify document hash
    doc_hash = f"sha3-256:{hashlib.sha3_256(plaintext).hexdigest()}"
    if doc_hash != req.document_hash:
        raise HTTPException(400, f"Document hash mismatch. Expected={req.document_hash[:32]}... Got={doc_hash[:32]}...")

    try:
        # 4. Generate watermark integrity tag
        integrity_input = (
            req.watermark_id + doc_hash + keypair.key_fingerprint + req.session_id
        ).encode("utf-8")
        integrity_tag = hmac.new(
            WATERMARK_SECRET, integrity_input, hashlib.sha3_256
        ).hexdigest()[:16]

        # 5. Create canonical decryption record (sorted keys, no whitespace)
        record = {
            "clientInstanceId": f"INST-{os.urandom(2).hex().upper()}",
            "documentHash": doc_hash,
            "documentId": req.document_id,
            "encryptionAlgorithm": "AES-256-GCM",
            "kemAlgorithm": "ML-KEM-768",
            "recipientId": keypair.recipient_id,
            "recipientKeyFingerprint": keypair.key_fingerprint,
            "sessionId": req.session_id,
            "signatureAlgorithm": "ML-DSA-65",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "watermarkAlgorithm": "DCT-BLIND-128",
            "watermarkId": req.watermark_id,
            "watermarkIntegrityTag": integrity_tag,
        }

        # Canonical serialization
        canonical_bytes = json.dumps(
            record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

        # 6. Sign with local ML-DSA private key (simulated with Ed25519)
        dsa_private = ed25519.Ed25519PrivateKey.from_private_bytes(keypair.dsa_private_key)
        signature = dsa_private.sign(canonical_bytes)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Watermark/signing step failed: {e}")

    # 7. Return plaintext + signed evidence
    decrypted_b64 = base64.b64encode(plaintext).decode()

    logger.info(
        f"Decryption complete for {req.callsign}: "
        f"session={req.session_id}, watermark={req.watermark_id}"
    )

    return DecryptResponse(
        session_id=req.session_id,
        document_id=req.document_id,
        watermark_id=req.watermark_id,
        canonical_record=record,
        recipient_signature=base64.b64encode(signature).decode(),
        signature_algorithm="ML-DSA-65",
        decrypted_document_b64=decrypted_b64,
        success=True,
        message=f"Document decrypted and signed by {req.callsign}",
    )

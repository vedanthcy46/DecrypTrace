import os
import random
import string
import base64
import json
import hashlib
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from backend.db.database import get_db
from backend.models.document import Document
from backend.models.recipient import Recipient
from backend.models.session import DecryptionSession
from backend.schemas import PrepareDecryptionResponse, SubmitEvidenceRequest, DecryptionSessionResponse
from backend.config import settings

logger = logging.getLogger("decryptrace.decryption")

router = APIRouter()

def generate_watermark_id():
    chars = string.ascii_uppercase + string.digits
    rand_part = ''.join(random.choice(chars) for _ in range(8))
    return f"WM-{rand_part}"

def generate_session_id():
    chars = string.ascii_uppercase + string.digits
    rand_part = ''.join(random.choice(chars) for _ in range(4))
    return f"SES-{rand_part}"

@router.post("/prepare/{doc_id}", response_model=PrepareDecryptionResponse)
async def prepare_decryption(doc_id: str, recipient_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    doc_result = await db.execute(select(Document).filter(Document.id == doc_id))
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    rec_result = await db.execute(select(Recipient).filter(Recipient.id == recipient_id))
    recipient = rec_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
        
    if document.status != "encrypted" or not document.encrypted_path:
        raise HTTPException(status_code=400, detail="Document is not encrypted")
        
    # Read encrypted document
    try:
        with open(document.encrypted_path, "rb") as f:
            enc_data = f.read()
    except Exception:
        raise HTTPException(status_code=500, detail="Could not read encrypted document")
        
    enc_b64 = base64.b64encode(enc_data).decode('utf-8')
    
    session_id = generate_session_id()
    watermark_id = generate_watermark_id()
    
    # Create session
    session = DecryptionSession(
        session_id=session_id,
        document_id=doc_id,
        recipient_id=recipient_id,
        watermark_id=watermark_id,
        status="prepared"
    )
    
    db.add(session)
    await db.commit()
    
    # Find the envelope for this recipient
    envelope = None
    for env in document.envelopes:
        if env["recipient_id"] == recipient_id:
            envelope = env
            break
            
    if not envelope:
        raise HTTPException(status_code=403, detail="Recipient not authorized for this document")

    return PrepareDecryptionResponse(
        session_id=session_id,
        document_id=doc_id,
        encrypted_document_b64=enc_b64,
        kem_ciphertext_b64=envelope["kem_ciphertext"],
        wrapped_dek_b64=envelope["wrapped_dek"],
        kek_nonce_b64=envelope["kek_nonce"],
        nonce_b64=envelope["nonce"],
        document_hash=document.document_hash,
        watermark_id=watermark_id
    )

@router.post("/sessions")
async def create_session(db: AsyncSession = Depends(get_db)):
    # Internal route if needed standalone
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/{session_id}/submit-evidence")
async def submit_evidence(session_id: str, request: SubmitEvidenceRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DecryptionSession).filter(DecryptionSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    rec_result = await db.execute(select(Recipient).filter(Recipient.id == session.recipient_id))
    recipient = rec_result.scalar_one_or_none()
    
    # Canonicalize and hash record
    canonical_bytes = json.dumps(request.canonical_record, separators=(',', ':'), sort_keys=True).encode('utf-8')
    hasher = hashlib.sha3_256()
    hasher.update(canonical_bytes)
    record_hash = hasher.hexdigest()
    
    # Verify ML-DSA signature (simulated with Ed25519)
    try:
        pub_key_bytes = base64.b64decode(recipient.ml_dsa_public_key)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
        sig_bytes = base64.b64decode(request.recipient_signature)
        pub_key.verify(sig_bytes, canonical_bytes)
        logger.info(f"✅ Signature verified for session {session_id}")
    except InvalidSignature:
        raise HTTPException(status_code=400, detail="Invalid ML-DSA signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signature verification error: {e}")
        
    session.recipient_signature = request.recipient_signature
    session.canonical_record_hash = f"sha3-256:{record_hash}"
    session.client_instance_id = request.client_instance_id
    session.status = "evidence_submitted"
    
    await db.commit()
    return {"status": "evidence_accepted", "session_id": session_id}

@router.post("/{session_id}/commit")
async def commit_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DecryptionSession).filter(DecryptionSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != "evidence_submitted":
        raise HTTPException(status_code=400, detail="Evidence not yet submitted")
    
    # Build transaction for DLT
    transaction = {
        "type": "DECRYPTION_EVENT",
        "payload": {
            "sessionId": session.session_id,
            "documentId": session.document_id,
            "recipientId": session.recipient_id,
            "watermarkId": session.watermark_id,
            "canonicalRecordHash": session.canonical_record_hash,
        },
        "recipientSignature": session.recipient_signature,
        "signatureAlgorithm": session.signature_algorithm,
    }

    # Submit to DLT nodes
    block_index = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get latest block from first available node
            latest_resp = None
            for node_url in settings.DLT_NODES:
                try:
                    resp = await client.get(f"{node_url}/chain/latest")
                    if resp.status_code == 200:
                        latest_resp = resp.json()
                        break
                except Exception:
                    continue

            from backend.core.dlt.block import Block
            import time

            prev_hash = latest_resp["hash"] if latest_resp else "0"
            idx = (latest_resp["index"] + 1) if latest_resp else 0

            block = Block(
                index=idx,
                timestamp=datetime.now(timezone.utc).isoformat(),
                sequence_number=idx,
                transactions=[transaction],
                previous_hash=prev_hash,
                hash="",
                endorsements=[],
            )
            block.hash = block._calculate_hash()

            # Collect endorsements (2-of-3 quorum)
            endorsements = []
            for node_url in settings.DLT_NODES:
                try:
                    resp = await client.post(
                        f"{node_url}/propose", json=block.to_dict()
                    )
                    if resp.status_code == 200:
                        endorsements.append(resp.json())
                except Exception:
                    continue

            if len(endorsements) >= settings.DLT_QUORUM_THRESHOLD:
                block.endorsements = endorsements
                # Commit to all nodes
                for node_url in settings.DLT_NODES:
                    try:
                        await client.post(f"{node_url}/commit", json=block.to_dict())
                    except Exception:
                        continue
                block_index = block.index
                logger.info(f"✅ Block #{block_index} committed with {len(endorsements)} endorsements")
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Quorum not met: {len(endorsements)}/{settings.DLT_QUORUM_THRESHOLD}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DLT commit failed: {e}")
        raise HTTPException(status_code=503, detail=f"DLT commit failed: {e}")
        
    session.ledger_committed = True
    session.ledger_block_index = block_index
    session.status = "committed"
    session.committed_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {"status": "committed", "ledger_block_index": block_index}

@router.get("/sessions", response_model=list[DecryptionSessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DecryptionSession))
    sessions = result.scalars().all()
    
    return [
        DecryptionSessionResponse(
            session_id=s.session_id,
            document_id=s.document_id,
            recipient_id=s.recipient_id,
            watermark_id=s.watermark_id,
            status=s.status,
            ledger_committed=s.ledger_committed,
            ledger_block_index=s.ledger_block_index,
            created_at=s.created_at
        )
        for s in sessions
    ]

@router.get("/sessions/{id}")
async def get_session(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DecryptionSession).filter(DecryptionSession.session_id == id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

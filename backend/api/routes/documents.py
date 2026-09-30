import uuid
import hashlib
import os
import base64
import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from backend.db.database import get_db
from backend.models.document import Document
from backend.models.recipient import Recipient
from backend.schemas import DocumentUploadResponse, DocumentEncryptRequest, DocumentEncryptResponse, DocumentListItem
from backend.config import settings
from backend.core.crypto import aes_gcm, ml_kem
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

router = APIRouter()

@router.post("/", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    temp_path = settings.STORAGE_DIR / f"{file_id}.pdf"
    
    content = await file.read()
    
    # Compute SHA3-256 hash
    doc_hash = f"sha3-256:{hashlib.sha3_256(content).hexdigest()}"
    
    with open(temp_path, "wb") as f:
        f.write(content)
        
    # Count pages
    try:
        doc = fitz.open(str(temp_path))
        page_count = doc.page_count
        doc.close()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF file")
        
    document = Document(
        id=file_id,
        title=file.filename,
        original_filename=file.filename,
        document_hash=doc_hash,
        file_size=len(content),
        page_count=page_count,
        status="uploaded"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        original_filename=document.original_filename,
        document_hash=document.document_hash,
        file_size=document.file_size,
        page_count=document.page_count,
        status=document.status,
        created_at=document.created_at
    )

@router.post("/{id}/encrypt", response_model=DocumentEncryptResponse)
async def encrypt_document(id: str, request: DocumentEncryptRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).filter(Document.id == id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    temp_path = settings.STORAGE_DIR / f"{document.id}.pdf"
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Original document file not found")
        
    # Read original document
    with open(temp_path, "rb") as f:
        plaintext = f.read()

    # AES-256-GCM Encryption
    payload = aes_gcm.encrypt(plaintext)
    
    # Save encrypted document
    encrypted_path = settings.ENCRYPTED_DIR / f"{document.id}.enc"
    with open(encrypted_path, "wb") as f:
        f.write(payload.to_bytes())

    # Get recipients and encapsulate AES key for each
    envelopes = []
    
    for rec_id in request.recipient_ids:
        rec_result = await db.execute(select(Recipient).filter(Recipient.id == rec_id))
        recipient = rec_result.scalar_one_or_none()
        if not recipient:
            raise HTTPException(status_code=400, detail=f"Recipient {rec_id} not found")
        
        # ML-KEM encapsulate to get a shared secret
        kem_result = ml_kem.encapsulate(
            base64.b64decode(recipient.ml_kem_public_key)
        )
        
        # Derive KEK from shared secret
        kek = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"simulation_kem",
        ).derive(kem_result.shared_secret)
        
        # Wrap the DEK (payload.key) using KEK
        kek_nonce = os.urandom(12)
        kek_gcm = AESGCM(kek)
        wrapped_dek = kek_gcm.encrypt(kek_nonce, payload.key, None)
        
        envelopes.append({
            "recipient_id": recipient.id,
            "callsign": recipient.callsign,
            "kem_ciphertext": kem_result.ciphertext_b64(),
            "wrapped_dek": base64.b64encode(wrapped_dek).decode(),
            "kek_nonce": base64.b64encode(kek_nonce).decode(),
            "nonce": base64.b64encode(payload.nonce).decode(),
            "kem_algorithm": "ML-KEM-768",
        })
        
    document.encrypted_path = str(encrypted_path)
    document.status = "encrypted"
    document.recipient_count = len(envelopes)
    document.envelopes = envelopes
    document.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return DocumentEncryptResponse(
        document_id=document.id,
        status=document.status,
        recipient_count=document.recipient_count,
        envelopes=envelopes
    )

@router.get("/", response_model=list[DocumentListItem])
async def list_documents(recipient_id: str | None = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document))
    documents = result.scalars().all()
    
    # Filter by recipient if provided — only show documents this recipient is authorized for
    if recipient_id:
        authorized = []
        for doc in documents:
            envelopes = doc.envelopes or []
            if any(env.get("recipient_id") == recipient_id for env in envelopes):
                authorized.append(doc)
        documents = authorized
    
    return [
        DocumentListItem(
            id=doc.id,
            title=doc.title,
            version=doc.version,
            status=doc.status,
            recipient_count=doc.recipient_count,
            encryption_algorithm=doc.encryption_algorithm,
            created_at=doc.created_at
        )
        for doc in documents
        if doc.status == "encrypted"
    ]

@router.get("/{id}")
async def get_document(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).filter(Document.id == id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return document

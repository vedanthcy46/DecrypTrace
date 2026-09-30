import hashlib
import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.recipient import Recipient
from backend.schemas import RecipientRegisterRequest, RecipientResponse

router = APIRouter()

@router.post("/", response_model=RecipientResponse)
async def register_recipient(request: RecipientRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Validate base64 inputs
    try:
        ml_dsa_bytes = base64.b64decode(request.ml_dsa_public_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ml_dsa_public_key base64 string")
        
    # Compute SHA3-256 fingerprint
    hasher = hashlib.sha3_256()
    hasher.update(ml_dsa_bytes)
    fingerprint = hasher.hexdigest()
    
    # Check if callsign exists (allow updating for demo purposes)
    existing = await db.execute(select(Recipient).filter(Recipient.callsign == request.callsign))
    recipient = existing.scalar_one_or_none()
    
    if recipient:
        recipient.ml_kem_public_key = request.ml_kem_public_key
        recipient.ml_dsa_public_key = request.ml_dsa_public_key
        recipient.key_fingerprint = fingerprint
    else:
        recipient = Recipient(
            name=request.name,
            callsign=request.callsign,
            email=request.email,
            ml_kem_public_key=request.ml_kem_public_key,
            ml_dsa_public_key=request.ml_dsa_public_key,
            key_fingerprint=fingerprint
        )
        db.add(recipient)
        
    await db.commit()
    await db.refresh(recipient)
    
    return RecipientResponse(
        id=recipient.id,
        name=recipient.name,
        callsign=recipient.callsign,
        email=recipient.email,
        key_fingerprint=recipient.key_fingerprint,
        status=recipient.status,
        created_at=recipient.created_at
    )

@router.get("/", response_model=list[RecipientResponse])
async def list_recipients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recipient))
    recipients = result.scalars().all()
    
    return [
        RecipientResponse(
            id=rec.id,
            name=rec.name,
            callsign=rec.callsign,
            email=rec.email,
            key_fingerprint=rec.key_fingerprint,
            status=rec.status,
            created_at=rec.created_at
        )
        for rec in recipients
    ]

@router.get("/{id}")
async def get_recipient(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recipient).filter(Recipient.id == id))
    recipient = result.scalar_one_or_none()
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
        
    return recipient

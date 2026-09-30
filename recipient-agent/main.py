"""
DecrypTrace — Recipient Agent

A LOCAL service that runs on the recipient's machine.
Handles all private-key operations:
  - ML-KEM decapsulation
  - AES-GCM decryption
  - Watermark embedding
  - Canonical record creation
  - ML-DSA signing

SECURITY: Private keys NEVER leave this environment.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RecipientAgent] %(levelname)s: %(message)s",
)
logger = logging.getLogger("recipient-agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Agent startup/shutdown."""
    logger.info("🔐 Recipient Agent starting...")
    logger.info("🔑 Private keys are stored locally and never transmitted")
    # Ensure keystore directory exists
    os.makedirs("keystore", exist_ok=True)
    yield
    logger.info("🛑 Recipient Agent shutting down")


app = FastAPI(
    title="DecrypTrace Recipient Agent",
    version="0.1.0",
    description="Local cryptographic agent — private keys never leave this device.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routes
from routes import router
app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "recipient-agent",
        "private_keys_local": True,
        "capabilities": ["ML-KEM-768", "ML-DSA-65", "AES-256-GCM", "DCT-Watermark"],
    }

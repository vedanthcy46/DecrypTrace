"""
DecrypTrace — Main FastAPI Application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import init_db
from backend.api.routes import documents, recipients, decryption, forensics, ledger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("decryptrace")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("🚀 DecrypTrace Backend starting...")
    await init_db()
    logger.info("📦 Database initialized")
    logger.info(f"🔐 Crypto: {settings.KEM_ALGORITHM} + {settings.DSA_ALGORITHM}")
    logger.info(f"🔗 DLT Nodes: {settings.DLT_NODES}")
    yield
    logger.info("🛑 DecrypTrace Backend shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Decryption-Time Forensic Attribution System. "
        "Cryptographically links leaked documents to specific decryption events."
    ),
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(recipients.router, prefix="/api/recipients", tags=["Recipients"])
app.include_router(decryption.router, prefix="/api/decryption", tags=["Decryption"])
app.include_router(forensics.router, prefix="/api/forensics", tags=["Forensics"])
app.include_router(ledger.router, prefix="/api/ledger", tags=["Ledger"])


@app.get("/api/health")
async def health_check():
    """System health check."""
    from backend.core.crypto import ml_kem
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "crypto": {
            "kem": settings.KEM_ALGORITHM,
            "dsa": settings.DSA_ALGORITHM,
            "symmetric": settings.SYMMETRIC_ALGORITHM,
            "real_pqc": ml_kem.is_real_implementation(),
        },
        "dlt_nodes": len(settings.DLT_NODES),
        "quorum_threshold": settings.DLT_QUORUM_THRESHOLD,
    }

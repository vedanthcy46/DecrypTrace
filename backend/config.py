"""
DecrypTrace Backend — Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """Application configuration."""

    # Application
    APP_NAME: str = "DecrypTrace"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./decryptrace.db"

    # Storage paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    ENCRYPTED_DIR: Path = BASE_DIR / "storage" / "encrypted"
    DECRYPTED_DIR: Path = BASE_DIR / "storage" / "decrypted"
    LEAKED_DIR: Path = BASE_DIR / "storage" / "leaked"

    # DLT nodes
    DLT_NODES: list[str] = [
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
    ]
    DLT_QUORUM_THRESHOLD: int = 2  # 2-of-3 quorum

    # Watermark
    WATERMARK_SECRET: str = "decryptrace-watermark-secret-change-in-production"
    WATERMARK_BITS: int = 128  # 128-bit watermark payload

    # Crypto
    KEM_ALGORITHM: str = "ML-KEM-768"
    DSA_ALGORITHM: str = "ML-DSA-65"
    SYMMETRIC_ALGORITHM: str = "AES-256-GCM"
    HASH_ALGORITHM: str = "SHA3-256"

    class Config:
        env_file = ".env"
        env_prefix = "DECRYPTRACE_"


settings = Settings()

# Ensure storage directories exist
for dir_path in [settings.STORAGE_DIR, settings.ENCRYPTED_DIR,
                 settings.DECRYPTED_DIR, settings.LEAKED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

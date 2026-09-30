"""
DecrypTrace — AES-256-GCM Symmetric Encryption

Used for encrypting document content. The AES key is then
protected per-recipient using ML-KEM key encapsulation.
"""
import os
import base64
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class EncryptedPayload:
    """Result of AES-GCM encryption."""
    nonce: bytes        # 12-byte nonce
    ciphertext: bytes   # Encrypted data + GCM tag
    key: bytes          # 32-byte AES key (only available during encryption)

    def to_dict(self) -> dict:
        return {
            "nonce": base64.b64encode(self.nonce).decode(),
            "ciphertext": base64.b64encode(self.ciphertext).decode(),
        }

    def to_bytes(self) -> bytes:
        """Serialize nonce + ciphertext for storage."""
        # Format: [12 bytes nonce][remaining ciphertext]
        return self.nonce + self.ciphertext

    @staticmethod
    def from_bytes(data: bytes) -> tuple[bytes, bytes]:
        """Deserialize stored data into (nonce, ciphertext)."""
        return data[:12], data[12:]


def generate_key() -> bytes:
    """Generate a random 256-bit AES key."""
    return os.urandom(32)


def encrypt(plaintext: bytes, key: bytes | None = None) -> EncryptedPayload:
    """
    Encrypt data using AES-256-GCM.

    Args:
        plaintext: Data to encrypt.
        key: Optional 32-byte key. Generated if not provided.

    Returns:
        EncryptedPayload with nonce, ciphertext, and key.
    """
    if key is None:
        key = generate_key()

    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    return EncryptedPayload(nonce=nonce, ciphertext=ciphertext, key=key)


def decrypt(nonce: bytes, ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt AES-256-GCM encrypted data.

    Args:
        nonce: 12-byte nonce used during encryption.
        ciphertext: Encrypted data including GCM tag.
        key: 32-byte AES key.

    Returns:
        Decrypted plaintext bytes.

    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

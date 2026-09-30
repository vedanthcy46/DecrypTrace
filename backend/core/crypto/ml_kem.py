"""
DecrypTrace — ML-KEM Key Encapsulation (Sender-side only)

This module handles the SENDER-SIDE operations:
- Encapsulating the AES symmetric key for each recipient's public key.

The RECIPIENT-SIDE decapsulation happens in the recipient-agent,
where the private key resides.

Uses ML-KEM-768 (FIPS 203) via pyca/cryptography.

FALLBACK: If pyca/cryptography doesn't have ML-KEM support in the
installed version, falls back to a simulation layer that clearly
marks itself as simulated.
"""
import base64
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import real ML-KEM from pyca/cryptography
_USE_REAL_KEM = False
try:
    from cryptography.hazmat.primitives.asymmetric import ml_kem
    _USE_REAL_KEM = True
    logger.info("ML-KEM: Using pyca/cryptography native implementation")
except ImportError:
    logger.warning(
        "ML-KEM: pyca/cryptography ML-KEM not available. "
        "Using simulation layer. Upgrade cryptography to v48.0.0+."
    )


@dataclass
class KEMKeyPair:
    """ML-KEM key pair."""
    public_key_bytes: bytes
    private_key_bytes: bytes  # Only used on recipient side
    algorithm: str = "ML-KEM-768"

    def public_key_b64(self) -> str:
        return base64.b64encode(self.public_key_bytes).decode()

    def private_key_b64(self) -> str:
        return base64.b64encode(self.private_key_bytes).decode()


@dataclass
class KEMEncapsulationResult:
    """Result of ML-KEM encapsulation."""
    ciphertext: bytes       # KEM ciphertext (send to recipient)
    shared_secret: bytes    # Shared secret (use as AES key or derive from)
    algorithm: str = "ML-KEM-768"

    def ciphertext_b64(self) -> str:
        return base64.b64encode(self.ciphertext).decode()


def generate_keypair() -> KEMKeyPair:
    """
    Generate an ML-KEM-768 key pair.

    NOTE: In the real architecture, this runs on the RECIPIENT DEVICE only.
    The backend only sees the public key.
    """
    if _USE_REAL_KEM:
        private_key = ml_kem.MLKEM768PrivateKey.generate()
        public_key = private_key.public_key()
        return KEMKeyPair(
            public_key_bytes=public_key.public_bytes_raw(),
            private_key_bytes=private_key.private_bytes_raw(),
        )
    else:
        # Simulation: generate random bytes of appropriate sizes
        # ML-KEM-768: public key = 1184 bytes, private key = 2400 bytes
        return KEMKeyPair(
            public_key_bytes=os.urandom(1184),
            private_key_bytes=os.urandom(2400),
        )


def encapsulate(public_key_bytes: bytes) -> KEMEncapsulationResult:
    """
    Encapsulate a shared secret using the recipient's ML-KEM public key.
    """
    if _USE_REAL_KEM:
        public_key = ml_kem.MLKEM768PublicKey.from_public_bytes(public_key_bytes)
        shared_secret, ciphertext = public_key.encapsulate()
        return KEMEncapsulationResult(
            ciphertext=ciphertext,
            shared_secret=shared_secret,
        )
    else:
        # Simulation: Use X25519 ECIES
        from cryptography.hazmat.primitives.asymmetric import x25519
        ephemeral_private = x25519.X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()
        recipient_public = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
        shared_secret = ephemeral_private.exchange(recipient_public)
        
        return KEMEncapsulationResult(
            ciphertext=ephemeral_public.public_bytes_raw(),
            shared_secret=shared_secret,
        )


def decapsulate(private_key_bytes: bytes, ciphertext: bytes) -> bytes:
    """
    Decapsulate to recover the shared secret.

    NOTE: This function exists here for completeness/testing.
    In the real architecture, decapsulation runs in the RECIPIENT AGENT.

    Args:
        private_key_bytes: Recipient's ML-KEM-768 private key (raw bytes).
        ciphertext: KEM ciphertext from encapsulation.

    Returns:
        32-byte shared secret.
    """
    if _USE_REAL_KEM:
        private_key = ml_kem.MLKEM768PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.decapsulate(ciphertext)
    else:
        # Simulation: return random bytes (won't match encapsulate)
        logger.warning("ML-KEM decapsulate: SIMULATED — result won't match encapsulate")
        return os.urandom(32)


def is_real_implementation() -> bool:
    """Check if we're using real ML-KEM or simulation."""
    return _USE_REAL_KEM

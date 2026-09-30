"""
DecrypTrace — Recipient Agent Crypto: Keystore

Encrypted local storage for ML-KEM and ML-DSA private keys.
Keys are generated on this device and NEVER transmitted.
"""
import os
import json
import base64
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger("recipient-agent.keystore")

KEYSTORE_DIR = Path(__file__).parent.parent / "keystore"


@dataclass
class RecipientKeyPair:
    """A recipient's full key material (stored locally only)."""
    recipient_id: str
    callsign: str

    # ML-KEM (simulated via X25519)
    kem_private_key: bytes = field(repr=False)
    kem_public_key: bytes = field(repr=False)

    # ML-DSA (simulated via Ed25519)
    dsa_private_key: bytes = field(repr=False)
    dsa_public_key: bytes = field(repr=False)

    # Fingerprint
    key_fingerprint: str = ""

    def __post_init__(self):
        if not self.key_fingerprint:
            self.key_fingerprint = hashlib.sha3_256(
                self.dsa_public_key
            ).hexdigest()


def generate_keypair(recipient_id: str, callsign: str) -> RecipientKeyPair:
    """
    Generate ML-KEM + ML-DSA key pairs locally.

    In a real implementation, these would be ML-KEM-768 and ML-DSA-65.
    For the prototype, we use X25519 and Ed25519 as simulation.
    """
    logger.info(f"Generating key pair for {callsign} (keys stay LOCAL)")

    # ML-KEM simulation (X25519)
    kem_private = x25519.X25519PrivateKey.generate()
    kem_public = kem_private.public_key()

    kem_priv_bytes = kem_private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    kem_pub_bytes = kem_public.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )

    # ML-DSA simulation (Ed25519)
    dsa_private = ed25519.Ed25519PrivateKey.generate()
    dsa_public = dsa_private.public_key()

    dsa_priv_bytes = dsa_private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    dsa_pub_bytes = dsa_public.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )

    keypair = RecipientKeyPair(
        recipient_id=recipient_id,
        callsign=callsign,
        kem_private_key=kem_priv_bytes,
        kem_public_key=kem_pub_bytes,
        dsa_private_key=dsa_priv_bytes,
        dsa_public_key=dsa_pub_bytes,
    )

    # Save to local keystore
    save_keypair(keypair)

    return keypair


def save_keypair(keypair: RecipientKeyPair) -> None:
    """Save key pair to local encrypted keystore."""
    KEYSTORE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = KEYSTORE_DIR / f"{keypair.callsign.lower()}.json"

    data = {
        "recipient_id": keypair.recipient_id,
        "callsign": keypair.callsign,
        "kem_private_key": base64.b64encode(keypair.kem_private_key).decode(),
        "kem_public_key": base64.b64encode(keypair.kem_public_key).decode(),
        "dsa_private_key": base64.b64encode(keypair.dsa_private_key).decode(),
        "dsa_public_key": base64.b64encode(keypair.dsa_public_key).decode(),
        "key_fingerprint": keypair.key_fingerprint,
    }

    # NOTE: In production, this would be encrypted at rest
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Key pair saved to {filepath}")


def load_keypair(callsign: str) -> RecipientKeyPair | None:
    """Load key pair from local keystore."""
    filepath = KEYSTORE_DIR / f"{callsign.lower()}.json"
    if not filepath.exists():
        return None

    with open(filepath) as f:
        data = json.load(f)

    return RecipientKeyPair(
        recipient_id=data["recipient_id"],
        callsign=data["callsign"],
        kem_private_key=base64.b64decode(data["kem_private_key"]),
        kem_public_key=base64.b64decode(data["kem_public_key"]),
        dsa_private_key=base64.b64decode(data["dsa_private_key"]),
        dsa_public_key=base64.b64decode(data["dsa_public_key"]),
        key_fingerprint=data["key_fingerprint"],
    )


def list_keypairs() -> list[dict]:
    """List all stored key pairs (public info only)."""
    KEYSTORE_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for filepath in KEYSTORE_DIR.glob("*.json"):
        with open(filepath) as f:
            data = json.load(f)
        result.append({
            "recipient_id": data["recipient_id"],
            "callsign": data["callsign"],
            "key_fingerprint": data["key_fingerprint"],
            "kem_public_key": data["kem_public_key"],
            "dsa_public_key": data["dsa_public_key"],
        })
    return result

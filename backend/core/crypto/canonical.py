"""
DecrypTrace — Canonical JSON Serialization

SECURITY REQUIREMENT: Decryption records MUST be serialized deterministically
before signing. The same logical record must always produce the same bytes,
regardless of where or when it is serialized.

This ensures any verifier can reconstruct exactly the same bytes from the
logical record and verify the ML-DSA signature.
"""
import json
import hashlib


def canonicalize(record: dict) -> bytes:
    """
    Produce a deterministic canonical byte representation of a record.

    Rules:
    - Keys sorted alphabetically (recursive)
    - No whitespace between separators
    - UTF-8 encoded
    - Consistent float/int representation

    Args:
        record: Dictionary to canonicalize.

    Returns:
        Deterministic UTF-8 bytes.
    """
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_hash(record: dict) -> str:
    """
    Produce the SHA3-256 hash of the canonical representation.

    Args:
        record: Dictionary to hash.

    Returns:
        Hex string of SHA3-256 hash, prefixed with "sha3-256:".
    """
    canonical_bytes = canonicalize(record)
    digest = hashlib.sha3_256(canonical_bytes).hexdigest()
    return f"sha3-256:{digest}"


def hash_bytes(data: bytes) -> str:
    """
    SHA3-256 hash of raw bytes.

    Args:
        data: Bytes to hash.

    Returns:
        Hex string prefixed with "sha3-256:".
    """
    digest = hashlib.sha3_256(data).hexdigest()
    return f"sha3-256:{digest}"


def verify_canonical_hash(record: dict, expected_hash: str) -> bool:
    """
    Verify that a record matches an expected canonical hash.

    Args:
        record: Dictionary to verify.
        expected_hash: Expected "sha3-256:..." hash string.

    Returns:
        True if hashes match.
    """
    return canonical_hash(record) == expected_hash

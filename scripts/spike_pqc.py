import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.exceptions import InvalidSignature

print("WARNING: Using SIMULATION LAYER for ML-KEM and ML-DSA as they are unavailable in the current cryptography version.")

class SimulatedMLKEM768PrivateKey:
    def __init__(self):
        self._key = x25519.X25519PrivateKey.generate()
        
    @classmethod
    def generate(cls):
        return cls()
        
    def public_key(self):
        return SimulatedMLKEM768PublicKey(self._key.public_key())
        
    def decapsulate(self, ciphertext):
        # In simulation, ciphertext is the ephemeral public key
        ephemeral_pub_bytes = ciphertext
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(ephemeral_pub_bytes)
        shared_key = self._key.exchange(ephemeral_pub)
        
        # Derive key to match KEM behavior
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"simulation_kem",
        ).derive(shared_key)
        
        return derived_key

class SimulatedMLKEM768PublicKey:
    def __init__(self, key):
        self._key = key
        
    def encapsulate(self):
        # Generate ephemeral keypair
        ephemeral_priv = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_priv.public_key()
        
        # Generate shared secret
        shared_key = ephemeral_priv.exchange(self._key)
        
        # Derive key
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"simulation_kem",
        ).derive(shared_key)
        
        ciphertext = ephemeral_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return ciphertext, derived_key
        
    def public_bytes(self, encoding, format):
        return self._key.public_bytes(encoding, format)

class SimulatedMLDSA65PrivateKey:
    def __init__(self):
        self._key = ed25519.Ed25519PrivateKey.generate()
        
    @classmethod
    def generate(cls):
        return cls()
        
    def public_key(self):
        return SimulatedMLDSA65PublicKey(self._key.public_key())
        
    def sign(self, data):
        return self._key.sign(data)

class SimulatedMLDSA65PublicKey:
    def __init__(self, key):
        self._key = key
        
    def verify(self, signature, data):
        self._key.verify(signature, data)


def test_ml_kem():
    print("\n--- Testing SIMULATED ML-KEM-768 ---")
    try:
        # Generate ML-KEM key pair
        private_key = SimulatedMLKEM768PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Encapsulate a shared secret
        ciphertext, shared_secret_sender = public_key.encapsulate()
        
        # Decapsulate and verify the secret matches
        shared_secret_receiver = private_key.decapsulate(ciphertext)
        
        if shared_secret_sender == shared_secret_receiver:
            print("PASS: Shared secrets match.")
        else:
            print("FAIL: Shared secrets do not match.")
            
        print(f"Public Key Size: {len(public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))} bytes")
        print(f"Ciphertext Size: {len(ciphertext)} bytes")
        print(f"Shared Secret Size: {len(shared_secret_sender)} bytes")
        
        return True, public_key, private_key
    except Exception as e:
        print(f"FAIL: ML-KEM test failed with error: {e}")
        return False, None, None

def test_ml_dsa():
    print("\n--- Testing SIMULATED ML-DSA-65 ---")
    try:
        # Generate ML-DSA key pair
        private_key = SimulatedMLDSA65PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Create a sample canonical decryption record
        record = {
            "action": "decrypt",
            "document_id": "doc_123",
            "timestamp": "2026-09-30T10:00:00Z",
            "user_id": "user_456"
        }
        # Canonical JSON with sorted keys, no whitespace
        canonical_record = json.dumps(record, separators=(',', ':'), sort_keys=True).encode('utf-8')
        
        # Sign the canonical bytes
        signature = private_key.sign(canonical_record)
        
        # Verify the signature -> PASS
        try:
            public_key.verify(signature, canonical_record)
            print("PASS: Signature verified successfully.")
        except InvalidSignature:
            print("FAIL: Valid signature failed verification.")
            
        # Modify the record, verify again -> FAIL (expected)
        modified_record = json.dumps({**record, "user_id": "user_999"}, separators=(',', ':'), sort_keys=True).encode('utf-8')
        try:
            public_key.verify(signature, modified_record)
            print("FAIL: Modified record verified successfully (should have failed).")
        except InvalidSignature:
            print("PASS: Modified record verification failed (expected).")
            
        # Verify with wrong public key -> FAIL (expected)
        wrong_private_key = SimulatedMLDSA65PrivateKey.generate()
        wrong_public_key = wrong_private_key.public_key()
        try:
            wrong_public_key.verify(signature, canonical_record)
            print("FAIL: Wrong public key verified successfully (should have failed).")
        except InvalidSignature:
            print("PASS: Wrong public key verification failed (expected).")
            
        return True
    except Exception as e:
        print(f"FAIL: ML-DSA test failed with error: {e}")
        return False

def test_aes_gcm():
    print("\n--- Testing AES-256-GCM ---")
    try:
        # Generate random 256-bit key
        key = os.urandom(32)
        aesgcm = AESGCM(key)
        
        # Encrypt sample data
        data = b"This is some sample document data that needs to be encrypted."
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # Decrypt and verify match
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
        
        if data == decrypted_data:
            print("PASS: AES-GCM encryption/decryption round-trip successful.")
            return True
        else:
            print("FAIL: Decrypted data does not match original data.")
            return False
    except Exception as e:
        print(f"FAIL: AES-GCM test failed with error: {e}")
        return False

def test_full_round_trip():
    print("\n--- Testing Full Round-Trip ---")
    try:
        # Keys setup
        kem_private = SimulatedMLKEM768PrivateKey.generate()
        kem_public = kem_private.public_key()
        dsa_private = SimulatedMLDSA65PrivateKey.generate()
        dsa_public = dsa_private.public_key()
        
        # ML-KEM encapsulate to get shared secret
        kem_ciphertext, shared_secret_sender = kem_public.encapsulate()
        
        # Data
        data = b"Confidential document content for the round-trip test."
        
        # Encrypt with shared secret
        aesgcm_sender = AESGCM(shared_secret_sender)
        nonce = os.urandom(12)
        encrypted_data = aesgcm_sender.encrypt(nonce, data, None)
        
        # Decapsulate to recover shared secret
        shared_secret_receiver = kem_private.decapsulate(kem_ciphertext)
        
        # Decrypt data
        aesgcm_receiver = AESGCM(shared_secret_receiver)
        decrypted_data = aesgcm_receiver.decrypt(nonce, encrypted_data, None)
        
        if data != decrypted_data:
            print("FAIL: Round-trip decrypted data mismatch.")
            return False
            
        # Sign the decryption record with ML-DSA
        record = {
            "action": "decrypt",
            "document_id": "doc_round_trip",
            "user_id": "agent_007",
            "success": True
        }
        canonical_record = json.dumps(record, separators=(',', ':'), sort_keys=True).encode('utf-8')
        signature = dsa_private.sign(canonical_record)
        
        # Verify signature
        try:
            dsa_public.verify(signature, canonical_record)
            print("PASS: Full round-trip successful.")
            return True
        except InvalidSignature:
            print("FAIL: Full round-trip signature verification failed.")
            return False
            
    except Exception as e:
        print(f"FAIL: Full round-trip test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("=== DecrypTrace PQC Spike Test ===")
    test_ml_kem()
    test_ml_dsa()
    test_aes_gcm()
    test_full_round_trip()
    print("\n=== Spike Test Complete ===")

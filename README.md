# DecrypTrace

> **Decryption-Time Forensic Attribution System**

One document. Many recipients. One leak. Cryptographic evidence of which decryption event produced it.

## What It Does

DecrypTrace solves a specific security problem: when the same encrypted document is distributed to multiple authorized recipients and one copy leaks, the system cryptographically links the leaked document back to the specific decryption event and the recipient signing key associated with it.

### The Attribution Chain

```
Sender encrypts document → Distribute to N recipients
→ Each recipient decrypts with unique forensic watermark
→ Decryption event signed with recipient's ML-DSA key
→ Signed evidence committed to replicated ledger
→ Document leaks
→ Extract watermark → Match ledger record → Verify signature
→ Forensic attribution confirmed
```

## Architecture

- **Frontend**: Next.js 15 + shadcn/ui + Tailwind CSS
- **Backend**: Python FastAPI (document management, forensic analysis)
- **Recipient Agent**: Local Python service (decryption, signing — private keys never leave device)
- **DLT**: 3-node quorum-based replicated permissioned ledger

### Cryptographic Standards
- **ML-KEM-768** (FIPS 203) — Key encapsulation
- **ML-DSA-65** (FIPS 204) — Digital signatures
- **AES-256-GCM** — Document encryption
- **SHA-3-256** — Hashing

## Quick Start

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 2. DLT Nodes
python -m dlt.node1 --port 8001
python -m dlt.node2 --port 8002
python -m dlt.node3 --port 8003

# 3. Recipient Agent
cd recipient-agent
pip install -r requirements.txt
uvicorn main:app --reload --port 8010

# 4. Frontend
cd frontend
npm install
npm run dev
```

## Security Properties

| Property | How It's Achieved |
|---|---|
| **Recipient key ownership** | Private keys generated & stored on recipient device only |
| **Forensic attribution** | Unique DCT watermark per decryption event |
| **Cryptographic evidence** | ML-DSA signature binds event to recipient signing key |
| **Tamper-evident audit** | 3-node replicated ledger with quorum-based commit |
| **Offline operation** | Entire system runs air-gapped, no cloud dependencies |

## License

MIT

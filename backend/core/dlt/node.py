from fastapi import FastAPI, HTTPException, Body
from typing import List, Dict, Any, Optional
import hmac
import hashlib

from backend.core.dlt.block import Block
from backend.core.dlt.chain import LedgerChain
from backend.core.crypto.canonical import canonical_hash

def create_app(node_id: str = "node1", port: int = 8001) -> FastAPI:
    app = FastAPI(title=f"DLT Node {node_id}")
    chain = LedgerChain()
    
    secret_key = f"secret_{node_id}".encode("utf-8")

    def _sign(message: str) -> str:
        return hmac.new(secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()

    @app.post("/propose")
    def propose(block_data: Dict[str, Any] = Body(...)):
        try:
            block = Block.from_dict(block_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid block data")

        latest = chain.get_latest_block()
        expected_prev_hash = latest.hash if latest else "0"
        if block.previous_hash != expected_prev_hash:
            raise HTTPException(status_code=400, detail="Previous hash mismatch")

        if block.hash != block._calculate_hash():
            raise HTTPException(status_code=400, detail="Block hash invalid")
        
        signature = _sign(block.hash)
        endorsement = {"nodeId": node_id, "nodeSignature": signature}
        return endorsement

    @app.post("/commit")
    def commit(block_data: Dict[str, Any] = Body(...)):
        try:
            block = Block.from_dict(block_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid block data")
            
        success = chain.add_block(block)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add block to chain")
        return {"status": "committed"}

    @app.get("/chain")
    def get_chain():
        return chain.to_dict_list()

    @app.get("/chain/latest")
    def get_latest():
        latest = chain.get_latest_block()
        if not latest:
            return None
        return latest.to_dict()

    @app.get("/chain/verify")
    def verify_chain():
        is_valid = chain.verify_integrity()
        return {"valid": is_valid}

    @app.get("/health")
    def health():
        return {"status": "ok", "node_id": node_id}

    @app.post("/tamper")
    def tamper(req: Dict[str, Any] = Body(...)):
        idx = req.get("index", 0)
        tx_idx = req.get("transaction_index", 0)
        key = req.get("key")
        val = req.get("value")
        
        block = chain.get_block(idx)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        
        if 0 <= tx_idx < len(block.transactions):
            block.transactions[tx_idx][key] = val
            return {"status": "tampered"}
        raise HTTPException(status_code=400, detail="Invalid transaction index")

    return app

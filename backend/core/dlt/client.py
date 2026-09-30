import httpx
import time
from typing import List, Dict, Any, Optional
from backend.core.crypto.canonical import canonical_hash

class DLTClient:
    def __init__(self, node_urls: List[str], quorum_threshold: int = 2):
        self.node_urls = node_urls
        self.quorum_threshold = quorum_threshold

    async def get_chain(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            for url in self.node_urls:
                try:
                    resp = await client.get(f"{url}/chain", timeout=2.0)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
                    continue
        return []

    async def get_latest_block(self) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            for url in self.node_urls:
                try:
                    resp = await client.get(f"{url}/chain/latest", timeout=2.0)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
                    continue
        return None

    async def submit_transaction(self, transaction: Dict[str, Any]) -> bool:
        latest_block = await self.get_latest_block()
        index = latest_block["index"] + 1 if latest_block else 0
        prev_hash = latest_block["hash"] if latest_block else "0"
        seq_num = latest_block.get("sequence_number", 0) + 1 if latest_block else 1

        block_content = {
            "index": index,
            "timestamp": str(time.time()),
            "sequence_number": seq_num,
            "transactions": [transaction],
            "previous_hash": prev_hash
        }
        b_hash = canonical_hash(block_content)
        
        block_data = {
            **block_content,
            "hash": b_hash,
            "endorsements": []
        }

        endorsements = []
        async with httpx.AsyncClient() as client:
            for url in self.node_urls:
                try:
                    resp = await client.post(f"{url}/propose", json=block_data, timeout=2.0)
                    if resp.status_code == 200:
                        endorsements.append(resp.json())
                except Exception:
                    continue

        if len(endorsements) >= self.quorum_threshold:
            block_data["endorsements"] = endorsements
            async with httpx.AsyncClient() as client:
                for url in self.node_urls:
                    try:
                        await client.post(f"{url}/commit", json=block_data, timeout=2.0)
                    except Exception:
                        pass
            return True
        return False

    async def get_block(self, index: int) -> Optional[Dict[str, Any]]:
        chain = await self.get_chain()
        if 0 <= index < len(chain):
            return chain[index]
        return None

    async def verify_cross_node(self) -> bool:
        chains = []
        async with httpx.AsyncClient() as client:
            for url in self.node_urls:
                try:
                    resp = await client.get(f"{url}/chain", timeout=2.0)
                    if resp.status_code == 200:
                        chains.append(resp.json())
                except Exception:
                    continue
        
        if not chains:
            return True
            
        base_chain = chains[0]
        for chain in chains[1:]:
            if len(base_chain) != len(chain):
                return False
            for b1, b2 in zip(base_chain, chain):
                if b1["hash"] != b2["hash"]:
                    return False
        return True

    async def simulate_tamper(self, node_index: int, block_index: int) -> bool:
        if 0 <= node_index < len(self.node_urls):
            url = self.node_urls[node_index]
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        f"{url}/tamper", 
                        json={"index": block_index, "transaction_index": 0, "key": "tampered", "value": True}
                    )
                    return resp.status_code == 200
                except Exception:
                    return False
        return False

    async def get_nodes_health(self) -> Dict[str, Any]:
        health_status = {}
        async with httpx.AsyncClient() as client:
            for url in self.node_urls:
                try:
                    resp = await client.get(f"{url}/health", timeout=2.0)
                    health_status[url] = resp.json() if resp.status_code == 200 else {"status": "down"}
                except Exception:
                    health_status[url] = {"status": "down"}
        return health_status

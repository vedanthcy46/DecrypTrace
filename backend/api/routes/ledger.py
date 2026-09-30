"""
DecrypTrace — Ledger API Routes

Provides access to the DLT ledger: block listing, cross-node
verification, tamper testing, and node health.
"""
import httpx
from fastapi import APIRouter, HTTPException
from backend.config import settings
from backend.schemas import LedgerBlockResponse, LedgerHealthResponse, TamperTestResponse

router = APIRouter()


@router.get("/blocks")
async def list_blocks():
    """Get all blocks from the first available DLT node."""
    if not settings.DLT_NODES:
        return []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for node_url in settings.DLT_NODES:
            try:
                resp = await client.get(f"{node_url}/chain")
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                continue
    return []


@router.get("/blocks/{index}")
async def get_block(index: int):
    """Get a specific block by index."""
    blocks = await list_blocks()
    for block in blocks:
        if block.get("index") == index:
            return block
    raise HTTPException(status_code=404, detail="Block not found")


@router.get("/verify")
async def verify_chain():
    """Cross-node chain verification — detect replica divergence."""
    chains = []
    node_results = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for node_url in settings.DLT_NODES:
            try:
                # Get chain from this node
                chain_resp = await client.get(f"{node_url}/chain")
                verify_resp = await client.get(f"{node_url}/chain/verify")

                if chain_resp.status_code == 200 and verify_resp.status_code == 200:
                    chain = chain_resp.json()
                    verify = verify_resp.json()
                    chains.append(chain)
                    node_results.append({
                        "node": node_url,
                        "chain_length": len(chain),
                        "local_integrity": verify.get("valid", False),
                        "latest_hash": chain[-1]["hash"][:16] + "..." if chain else "genesis",
                    })
                else:
                    node_results.append({
                        "node": node_url,
                        "chain_length": 0,
                        "local_integrity": False,
                        "latest_hash": "unreachable",
                    })
            except Exception:
                node_results.append({
                    "node": node_url,
                    "chain_length": 0,
                    "local_integrity": False,
                    "latest_hash": "unreachable",
                })

    # Cross-node comparison
    reachable_chains = [c for c in chains if c]
    all_match = True
    divergence_details = []

    # First, check local integrity of all nodes
    for node_res in node_results:
        if not node_res["local_integrity"]:
            all_match = False
            divergence_details.append(f"Node {node_res['node']} failed local integrity check (tampered)")

    if len(reachable_chains) >= 2:
        ref_length = len(reachable_chains[0])
        for i, chain in enumerate(reachable_chains[1:], 1):
            if len(chain) != ref_length:
                all_match = False
                divergence_details.append(f"Chain length mismatch: node 0 has {ref_length}, node {i} has {len(chain)}")
            else:
                for j in range(ref_length):
                    if chain[j]["hash"] != reachable_chains[0][j]["hash"]:
                        all_match = False
                        divergence_details.append(f"Block {j} hash diverges between nodes")
                        break

    return {
        "verified": all_match,
        "nodes_checked": len(node_results),
        "nodes_reachable": len(reachable_chains),
        "chain_length": len(reachable_chains[0]) if reachable_chains else 0,
        "node_details": node_results,
        "divergence": divergence_details if divergence_details else None,
    }


@router.post("/tamper-test")
async def tamper_test():
    """
    Simulate tampering on one node and verify detection.
    1. Tamper with Node 2's local chain
    2. Run cross-node verification
    3. Show divergence detected
    """
    if len(settings.DLT_NODES) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 nodes for tamper test")

    target_node = settings.DLT_NODES[1]  # Tamper Node 2

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check if there are blocks to tamper with
        try:
            chain_resp = await client.get(f"{target_node}/chain")
            if chain_resp.status_code != 200:
                raise HTTPException(status_code=503, detail="Cannot reach target node")
            chain = chain_resp.json()
            if not chain:
                return TamperTestResponse(
                    tamper_type="no_blocks",
                    node_targeted=target_node,
                    divergence_detected=False,
                    details="No blocks in chain to tamper with. Run the demo scenario first.",
                )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Cannot reach target node")

        # Tamper with the first block
        try:
            await client.post(f"{target_node}/tamper", json={
                "index": 0,
                "transaction_index": 0,
                "key": "type",
                "value": "TAMPERED_EVENT",
            })
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Tamper failed: {e}")

    # Now verify cross-node
    verification = await verify_chain()

    return TamperTestResponse(
        tamper_type="modify_transaction",
        node_targeted=target_node,
        divergence_detected=not verification["verified"],
        details=(
            f"Tampered Node 2. Cross-node verification: "
            f"{'DIVERGENCE DETECTED' if not verification['verified'] else 'No divergence (unexpected)'}. "
            f"Divergence details: {verification.get('divergence', 'none')}"
        ),
    )


@router.get("/nodes/health")
async def nodes_health():
    """Health check for all DLT nodes."""
    nodes_status = []
    total_chain_length = 0

    async with httpx.AsyncClient(timeout=3.0) as client:
        for node_url in settings.DLT_NODES:
            try:
                health_resp = await client.get(f"{node_url}/health")
                chain_resp = await client.get(f"{node_url}/chain")

                is_up = health_resp.status_code == 200
                chain_len = len(chain_resp.json()) if chain_resp.status_code == 200 else 0
                total_chain_length = max(total_chain_length, chain_len)

                node_data = health_resp.json() if is_up else {}
                nodes_status.append({
                    "url": node_url,
                    "node_id": node_data.get("node_id", "unknown"),
                    "status": "up" if is_up else "down",
                    "chain_length": chain_len,
                })
            except Exception:
                nodes_status.append({
                    "url": node_url,
                    "node_id": "unknown",
                    "status": "down",
                    "chain_length": 0,
                })

    return LedgerHealthResponse(
        nodes=nodes_status,
        chain_length=total_chain_length,
        integrity_verified=all(n["status"] == "up" for n in nodes_status),
    )

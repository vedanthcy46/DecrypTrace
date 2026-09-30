import hashlib
import json
import time
from typing import List, Dict, Any, Optional

def compute_hash(data: dict) -> str:
    # Use JSON canonical serialization (sorted keys, no whitespace)
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha3_256(serialized.encode('utf-8')).hexdigest()

class Block:
    def __init__(self, index: int, timestamp: str, transactions: list, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.endorsements = []
        self.hash = self._calculate_hash()
        
    def _calculate_hash(self) -> str:
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash
        }
        return compute_hash(block_content)

class Node:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.chain: List[Block] = []
        self.online = True
        
    def validate_proposal(self, block: Block) -> Optional[str]:
        if not self.online:
            return None
            
        # Check previous_hash matches last block's hash
        if self.chain:
            if block.previous_hash != self.chain[-1].hash:
                return None
        else:
            if block.previous_hash != "0":
                return None
                
        # Compute and verify block hash
        if block.hash != block._calculate_hash():
            return None
            
        # Endorse: simple signature mock for the spike
        return f"SIG_{self.node_id}_{block.hash[:8]}"

    def commit_block(self, block: Block):
        if not self.online:
            return False
        # Create a deep copy to ensure isolation between node local states
        new_block = Block(block.index, block.timestamp, json.loads(json.dumps(block.transactions)), block.previous_hash)
        new_block.endorsements = list(block.endorsements)
        new_block.hash = block.hash
        self.chain.append(new_block)
        return True

class Coordinator:
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        
    def propose_and_commit(self, transactions: list) -> bool:
        print(f"\n--- Proposing transactions: {transactions} ---")
        
        # Get current state from the first available node to build the block
        active_nodes = [n for n in self.nodes if n.online]
        if not active_nodes:
            print("FAIL: No nodes online")
            return False
            
        latest_block = active_nodes[0].chain[-1] if active_nodes[0].chain else None
        index = latest_block.index + 1 if latest_block else 0
        prev_hash = latest_block.hash if latest_block else "0"
        
        block = Block(
            index=index,
            timestamp=str(time.time()),
            transactions=transactions,
            previous_hash=prev_hash
        )
        
        # Collect endorsements
        endorsements = []
        for node in self.nodes:
            endorsement = node.validate_proposal(block)
            if endorsement:
                endorsements.append(endorsement)
                print(f"Received endorsement from {node.node_id}")
            else:
                print(f"No endorsement from {node.node_id}")
                
        # Check quorum (2-of-3)
        if len(endorsements) >= 2:
            print(f"Quorum reached with {len(endorsements)} endorsements.")
            block.endorsements = endorsements
            for node in self.nodes:
                node.commit_block(block)
            print("PASS: Block committed to all online nodes.")
            return True
        else:
            print(f"FAIL: Quorum failed. Only {len(endorsements)} endorsements received.")
            return False

def print_test_header(title):
    print(f"\n{'='*50}\nTEST: {title}\n{'='*50}")

def run_tests():
    node1 = Node("node1")
    node2 = Node("node2")
    node3 = Node("node3")
    nodes = [node1, node2, node3]
    
    coordinator = Coordinator(nodes)
    
    # 4. Test: Normal operation
    print_test_header("Normal operation")
    success = coordinator.propose_and_commit([{"event": "decryption", "user": "alice", "file": "secret.pdf"}])
    success = success and coordinator.propose_and_commit([{"event": "decryption", "user": "bob", "file": "data.pdf"}])
    
    if success and len(node1.chain) == 2 and node1.chain[1].hash == node2.chain[1].hash == node3.chain[1].hash:
        print("PASS: Normal operation successful. All 3 nodes have identical chains.")
    else:
        print("FAIL: Normal operation failed.")

    # 5. Test: Tamper detection
    print_test_header("Tamper detection")
    print("Modifying a transaction in node2's local chain directly...")
    node2.chain[0].transactions[0]["user"] = "eve"
    
    print("Running cross-node verification...")
    # Re-calculate hash for tampered block
    tampered_hash = node2.chain[0]._calculate_hash()
    
    if node1.chain[0].hash != tampered_hash:
        print(f"TAMPER DETECTED: Node2's recalculated hash ({tampered_hash[:8]}...) diverges from valid hash ({node1.chain[0].hash[:8]}...).")
        print("PASS: Tamper detection successfully identified divergence.")
    else:
        print("FAIL: Tamper detection failed.")
        
    # 6. Test: Quorum with one node down
    print_test_header("Quorum with one node down")
    print("Simulating node3 being unavailable...")
    node3.online = False
    
    success = coordinator.propose_and_commit([{"event": "decryption", "user": "charlie", "file": "report.pdf"}])
    if success:
        print("PASS: 2-of-3 quorum still succeeds with one node down.")
    else:
        print("FAIL: Quorum should have succeeded.")
        
    # 7. Test: Quorum failure
    print_test_header("Quorum failure")
    print("Simulating node2 also being unavailable...")
    node2.online = False
    
    success = coordinator.propose_and_commit([{"event": "decryption", "user": "dave", "file": "plans.pdf"}])
    if not success:
        print("PASS: 1-of-3 correctly fails quorum requirement.")
    else:
        print("FAIL: Quorum should have failed.")

if __name__ == '__main__':
    run_tests()

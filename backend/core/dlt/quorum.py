import time
from typing import List, Dict, Any
from .block import Block

class QuorumManager:
    def __init__(self, nodes: List[Any], threshold: int = 2):
        self.nodes = nodes
        self.threshold = threshold

    def propose_transaction(self, transaction: Dict[str, Any]) -> bool:
        active_nodes = [n for n in self.nodes if getattr(n, "online", True)]
        if not active_nodes:
            return False

        latest_block = None
        if active_nodes[0].chain.blocks:
            latest_block = active_nodes[0].chain.get_latest_block()
        
        index = latest_block.index + 1 if latest_block else 0
        prev_hash = latest_block.hash if latest_block else "0"
        seq_num = latest_block.sequence_number + 1 if latest_block else 1

        block = Block(
            index=index,
            timestamp=str(time.time()),
            sequence_number=seq_num,
            transactions=[transaction],
            previous_hash=prev_hash,
            hash="",
            endorsements=[]
        )
        block.hash = block._calculate_hash()

        endorsements = []
        for node in self.nodes:
            endorsement = node.validate_proposal(block)
            if endorsement:
                endorsements.append(endorsement)

        if len(endorsements) >= self.threshold:
            block.endorsements = endorsements
            for node in self.nodes:
                if getattr(node, "online", True):
                    node.commit_block(block)
            return True
        return False

    def verify_cross_node(self, nodes: List[Any]) -> bool:
        if not nodes:
            return True
        base_chain = nodes[0].chain.to_dict_list()
        for node in nodes[1:]:
            node_chain = node.chain.to_dict_list()
            if len(base_chain) != len(node_chain):
                return False
            for b1, b2 in zip(base_chain, node_chain):
                if b1["hash"] != b2["hash"]:
                    return False
        return True

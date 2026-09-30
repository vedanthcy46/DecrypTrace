from typing import List, Optional
from .block import Block
from backend.core.crypto.canonical import canonical_hash

class LedgerChain:
    def __init__(self):
        self.blocks: List[Block] = []

    def add_block(self, block: Block) -> bool:
        if not self.blocks:
            if block.previous_hash != "0":
                return False
        else:
            if block.previous_hash != self.blocks[-1].hash:
                return False

        if block.hash != block._calculate_hash():
            return False

        self.blocks.append(block)
        return True

    def get_latest_block(self) -> Optional[Block]:
        return self.blocks[-1] if self.blocks else None

    def verify_integrity(self) -> bool:
        for i, block in enumerate(self.blocks):
            if block.hash != block._calculate_hash():
                return False
            
            if i > 0:
                if block.previous_hash != self.blocks[i-1].hash:
                    return False
            else:
                if block.previous_hash != "0":
                    return False
        return True

    def get_block(self, index: int) -> Optional[Block]:
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None

    def to_dict_list(self) -> List[dict]:
        return [b.to_dict() for b in self.blocks]

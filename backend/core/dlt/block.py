from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from backend.core.crypto.canonical import canonical_hash

@dataclass
class Block:
    index: int
    timestamp: str
    sequence_number: int
    transactions: List[Dict[str, Any]]
    previous_hash: str
    hash: str
    endorsements: List[Dict[str, Any]]

    def _calculate_hash(self) -> str:
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash
        }
        return canonical_hash(block_content)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        return cls(**data)

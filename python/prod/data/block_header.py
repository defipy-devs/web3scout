# This dataclass was extracted from web3-ethereum-defi
# (https://github.com/Kartograf/web3-ethereum-defi)
# Licensed under the MIT License.
# Original copyright (c) 2023 Kartograf contributors.
#
# Extracted into web3scout to remove the eth_defi runtime dependency.
# Only the fields used by web3scout's reorg monitoring are included.

from dataclasses import dataclass, asdict
from typing import Optional
import pandas as pd

Timestamp = int

@dataclass(slots=True)
class BlockHeader:
    block_number: int
    block_hash: str
    timestamp: Optional[Timestamp] = None

    @staticmethod
    def to_pandas(data: list, partition_size: int = 0) -> pd.DataFrame:
        return pd.DataFrame(data)

    @staticmethod
    def from_pandas(df: pd.DataFrame) -> dict:
        block_map = {}
        for _, row in df.iterrows():
            bh = BlockHeader(
                block_number=int(row["block_number"]),
                block_hash=str(row["block_hash"]),
                timestamp=int(row["timestamp"]) if row.get("timestamp") is not None else None,
            )
            block_map[bh.block_number] = bh
        return block_map

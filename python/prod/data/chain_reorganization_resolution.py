from dataclasses import dataclass
from typing import Tuple

@dataclass(slots=True, frozen=True)
class ChainReorganizationResolution:
    """How did we fare getting hashes and timestamps for the latest blocks."""

    #: What we know is the chain tip on our node
    #:
    #: This is the latest block at the JSON-RPC node.
    #: We can read data up to this block.
    last_live_block: int

    #: What we know is the block for which we do not need to perform rollback
    #:
    #: This is the block number that does not need to purged from your internal database.
    #: All previously read events that have higher block number should be purged.
    #:
    latest_block_with_good_data: int

    #: Did we detect any reorgs in this chycle
    reorg_detected: bool

    def __repr__(self):
        return f"<reorg:{self.reorg_detected} last_live_block: {self.last_live_block:,}, latest_block_with_good_data:{self.latest_block_with_good_data:,}>"

    def get_read_range(self) -> Tuple[int, int]:
        """Get the range of blocks we should read on this poll cycle.

        - This range may overlap your previous event read range.

        - You should discard any data that's older than the start of the range

        - You should be prepared to read an event again

        :return:
            (start block, end block) inclusive range

        """
        assert self.last_live_block >= self.latest_block_with_good_data, f"Last block from the node: {self.last_live_block}, last block we have read: {self.latest_block_with_good_data}"
        return (self.latest_block_with_good_data + 1, self.last_live_block)

import logging
from web3 import Web3
from hexbytes import HexBytes
from typing import Iterable
from ...data.reorganization_monitor import ReorganizationMonitor

from eth_defi.event_reader.block_header import BlockHeader

logger = logging.getLogger(__name__)

class JSONRPCReorganizationMonitor(ReorganizationMonitor):
    """Watch blockchain for reorgs using eth_getBlockByNumber JSON-RPC API.

    - Use expensive eth_getBlockByNumber call to download
      block hash and timestamp from Ethereum compatible node
    """

    def __init__(self, web3: Web3, **kwargs):
        super().__init__(**kwargs)
        self.web3 = web3

    def __repr__(self):
        return f"<JSONRPCReorganisationMonitor, last_block_read: {self.last_block_read}>"

    def get_last_block_live(self):
        return self.web3.eth.block_number

    def fetch_block_data(self, start_block, end_block) -> Iterable[BlockHeader]:
        total = end_block - start_block
        logger.debug(f"Fetching block headers and timestamps for logs {start_block:,} - {end_block:,}, total {total:,} blocks")
        web3 = self.web3

        # Collect block timestamps from the headers
        for block_num in range(start_block, end_block + 1):
            response_json = web3.manager._make_request("eth_getBlockByNumber", (hex(block_num), False))
            raw_result = response_json["result"]

            # Happens the chain tip and https://polygon-rpc.com/
            # - likely the request routed to different backend node
            if raw_result is None:
                logger.debug("Abnormally terminated at block %d, chain tip unstable?", block_num)
                break

            data_block_number = raw_result["number"]

            block_hash = raw_result["hash"]
            if isinstance(block_hash, HexBytes):
                # Web3.py middleware madness
                block_hash = block_hash.hex()

            if type(data_block_number) == str:
                # Real node
                assert int(raw_result["number"], 16) == block_num
                timestamp = int(raw_result["timestamp"], 16)
            else:
                # EthereumTester
                timestamp = raw_result["timestamp"]

            record = BlockHeader(block_num, block_hash, timestamp)
            logger.debug("Fetched block record: %s, total %d transactions", record, len(raw_result["transactions"]))
            yield record
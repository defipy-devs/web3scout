"""High performance EVM event reader.

For further reading see:

- `Ethereum JSON-RPC API spec <https://playground.open-rpc.org/?schemaUrl=https://raw.githubusercontent.com/ethereum/execution-apis/assembled-spec/openrpc.json&uiSchema%5BappBar%5D%5Bui:splitView%5D=false&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false>`_

- `futureproof - - Bulletproof concurrent.futures for Python <https://github.com/yeraydiazdiaz/futureproof>`_

"""

import logging
from web3 import Web3
from web3.contract.contract import ContractEvent
from web3.datastructures import AttributeDict
from typing import Callable, Optional, Iterable, Dict, List
from eth_bloom import BloomFilter
from hexbytes import HexBytes

from ..tools.conversion import Conversion
from ..tools.log_context import LogContext
from ..tools.log_result import LogResult
from ...utils.progress_update import ProgressUpdate
from ...data.filter import Filter
from ...data.reorganization_monitor import ReorganizationMonitor

logger = logging.getLogger(__name__)

def extract_timestamps_json_rpc(
    web3: Web3,
    start_block: int,
    end_block: int,
) -> Dict[str, int]:
    """Get block timestamps from block headers.

    Use slow JSON-RPC block headers call to get this information.

    TODO: This is an old code path. This has been replaced by more robust
    :py:class:`ReorganisationMonitor` implementation.

    :return:
        block hash -> UNIX timestamp mapping
    """
    timestamps = {}
    convert = Conversion()

    logging.debug("Extracting timestamps for logs %d - %d", start_block, end_block)

    # Collect block timestamps from the headers
    for block_num in range(start_block, end_block + 1):
        raw_result = web3.manager.request_blocking("eth_getBlockByNumber", (hex(block_num), False))
        data_block_number = convert.convert_jsonrpc_value_to_int(raw_result["number"])
        assert data_block_number == block_num, "Blockchain node did not give us the block we want"
        timestamps[raw_result["hash"]] = convert.convert_jsonrpc_value_to_int(raw_result["timestamp"])

    return timestamps

class ReadEvents:

    def apply(
        self,
        web3: Web3,
        start_block: int,
        end_block: int,
        events: Optional[List[ContractEvent]] = None,
        notify: Optional[ProgressUpdate] = None,
        chunk_size: int = 100,
        context: Optional[LogContext] = None,
        extract_timestamps: Optional[Callable] = extract_timestamps_json_rpc,
        filter: Optional[Filter] = None,
        reorg_mon: Optional[ReorganizationMonitor] = None,
    ) -> Iterable[LogResult]:
        """Reads multiple events from the blockchain.
    
        Optimized to read multiple events from test blockchains.
    
        .. note ::
    
            For a much faster event reader check :py:class:`eth_defi.reader.multithread.MultithreadEventReader`.
            This implementation is mostly good with EVM test backends or very small block ranges.
    
        - Scans chains block by block
    
        - Returns events as a dict for optimal performance
    
        - Supports interactive progress bar
    
        - Reads all the events matching signature - any filtering must be done
          by the reader
    
        See `scripts/read-uniswap-v2-pairs-and-swaps.py` for a full example.
    
        Example:
    
        .. code-block:: python
    
            json_rpc_url = os.environ["JSON_RPC_URL"]
            web3 = Web3(HTTPProvider(json_rpc_url)
    
            web3.middleware_onion.clear()
    
            # Get contracts
            Factory = get_contract(web3, "sushi/UniswapV2Factory.json")
    
            start_block = 1
            end_block = web3.eth.block_number
    
            filter = Filter.create_filter(
                factory_address,
                [Factory.events.PairCreated],
            )
    
            # Read through all the events, all the chain, using a single threaded slow loop.
            # Only suitable for test EVM backends.
            pairs = []
            log: LogResult
            for log in read_events(
                web3,
                start_block,
                end_block,
                filter=filter,
                extract_timestamps=None,
            ):
                # Signature this
                #
                #  event PairCreated(address indexed token0, address indexed token1, address pair, uint);
                #
                # topic 0 = keccak(event signature)
                # topic 1 = token 0
                # topic 2 = token 1
                # argument 0 = pair
                # argument 1 = pair id
                #
                # log for EthereumTester backend is
                #
                # {'type': 'mined',
                #  'logIndex': 0,
                #  'transactionIndex': 0,
                #  'transactionHash': HexBytes('0x2cf4563f8c275e5b5d7a4e5496bfbaf15cc00d530f15f730ac4a0decbc01d963'),
                #  'blockHash': HexBytes('0x7c0c6363bc8f4eac452a37e45248a720ff09f330117cdfac67640d31d140dc38'),
                #  'blockNumber': 6,
                #  'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                #  'data': HexBytes('0x00000000000000000000000068931307edcb44c3389c507dab8d5d64d242e58f0000000000000000000000000000000000000000000000000000000000000001'),
                #  'topics': [HexBytes('0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'),
                #   HexBytes('0x0000000000000000000000002946259e0334f33a064106302415ad3391bed384'),
                #   HexBytes('0x000000000000000000000000b9816fc57977d5a786e654c7cf76767be63b966e')],
                #  'context': None,
                #  'event': web3._utils.datatypes.PairCreated,
                #  'chunk_id': 1,
                #  'timestamp': None}
                #
                arguments = decode_data(log["data"])
                topics = log["topics"]
                token0 = convert_uint256_hex_string_to_address(topics[1])
                token1 = convert_uint256_hex_string_to_address(topics[2])
                pair_address = convert_uint256_bytes_to_address(arguments[0])
                pair_id = convert_int256_bytes_to_int(arguments[1])
    
                token0_details = fetch_erc20_details(web3, token0)
                token1_details = fetch_erc20_details(web3, token1)
    
    
        :param web3:
            Web3 instance
    
        :param events:
            List of Web3.py contract event classes to scan for.
    
            Pass this or filter.
    
        :param notify:
            Optional callback to be called before starting to scan each chunk
    
        :param start_block:
            First block to process (inclusive)
    
        :param end_block:
            Last block to process (inclusive)
    
        :param extract_timestamps:
            Override for different block timestamp extraction methods.
    
            This might need to use expensive`eth_getBlockByNumber` JSON-RPC API call.
            It will seriously slow down event reading.
            Set `extract_timestamps` to `None` to not get timestamps, but fast event lookups.
    
        :param chunk_size:
            How many blocks to scan in one eth_getLogs call
    
        :param context:
            Passed to the all generated logs
    
        :param filter:
            Pass a custom event filter for the readers
    
            Pass this or events.
    
        :param reorg_mon:
            If passed, use this instance to monitor and raise chain reorganisation exceptions.
    
        :return:
            Iterate over :py:class:`LogResult` instances for each event matched in
            the filter.
        """
    
        assert type(start_block) == int
        assert type(end_block) == int
    
        total_events = 0
    
        # TODO: retry middleware makes an exception
        # assert len(web3.middleware_onion) == 0, f"Must not have any Web3 middleware installed to slow down scan, has {web3.middleware_onion.middlewares}"
    
        # Construct our bloom filter
        if filter is None:
            assert events is not None, "Cannot pass both filter and events"
            filter = prepare_filter(events)
    
        last_timestamp = None
    
        for block_num in range(start_block, end_block + 1, chunk_size):
            last_of_chunk = min(end_block, block_num + chunk_size - 1)
    
            logger.debug("Extracting eth_getLogs from %d - %d", block_num, last_of_chunk)
    
            batch_events = 0
    
            # Stream the events
            for event in self.extract_events(
                web3,
                block_num,
                last_of_chunk,
                filter,
                context,
                extract_timestamps,
                reorg_mon,
            ):
                last_timestamp = event.get("timestamp")
                total_events += 1
                batch_events += 1
                yield event
    
            # Ping our master,
            # only when we have an event hit not to cause unnecessary block header fetches
            # TODO: Add argument notify always
            if notify is not None and batch_events:
                notify(block_num, start_block, end_block, chunk_size, total_events, last_timestamp, context)


    def extract_events(
        self,
        web3: Web3,
        start_block: int,
        end_block: int,
        filter: Filter,
        context: Optional[LogContext] = None,
        extract_timestamps: Optional[Callable] = extract_timestamps_json_rpc,
        reorg_mon: Optional[ReorganizationMonitor] = None,
    ) -> Iterable[LogResult]:
        """Perform eth_getLogs call over a block range.
    
        You should use :py:func:`read_events` unless you know the block range is something your node can handle.
    
        :param start_block:
            First block to process (inclusive)
    
        :param end_block:
            Last block to process (inclusive)
    
        :param filter:
            Internal filter used to match logs
    
        :param extract_timestamps:
            Method to get the block timestamps.
    
            This might need to use expensive`eth_getBlockByNumber` JSON-RPC API call.
            It will seriously slow down event reading.
            Set `extract_timestamps` to `None` to not get timestamps, but fast event lookups.
    
    
        :param context:
            Passed to the all generated logs
    
        :param reorg_mon:
            If passed, use this instance to monitor and raise chain reorganisation exceptions.
    
        :return:
            Iterable for the raw event data
        """
    
        if reorg_mon:
            assert extract_timestamps is None, "You cannot pass both reorg_mon and extract_timestamps"
    
        topics = list(filter.topics.keys())
    
        # https://www.quicknode.com/docs/ethereum/eth_getLogs
        # https://docs.alchemy.com/alchemy/guides/eth_getlogs
        filter_params = {
            "topics": [topics],  # JSON-RPC has totally braindead API to say how to do OR event lookup
            "fromBlock": hex(start_block),
            "toBlock": hex(end_block),
        }
    
        # Do the filtering by address.
        # eth_getLogs gets single address or JSON list of addresses
        if filter.contract_address:
            assert type(filter.contract_address) in (list, str), f"Got: {type(filter.contract_address)}"
            filter_params["address"] = filter.contract_address
    
        # logging.debug("Extracting logs %s", filter_params)
        # logging.info("Log range %d - %d", start_block, end_block)
    
        try:
            logs = web3.manager.request_blocking("eth_getLogs", (filter_params,))
        except Exception as e:
            block_count = end_block - start_block
            raise ReadingLogsFailed(f"eth_getLogs failed for {start_block:,} - {end_block:,} (total {block_count:,} with filter {filter}") from e

        convert = Conversion()
        
        if logs:
            if extract_timestamps is not None:
                timestamps = extract_timestamps(web3, start_block, end_block)
                if timestamps is None:
                    raise BadTimestampValueReturned("extract_timestamps returned None")
            else:
                timestamps = None
    
            for log in logs:
                block_hash = log["blockHash"]
                block_number = convert.convert_jsonrpc_value_to_int(log["blockNumber"])
                # Retrofit our information to the dict
                event_signature = log["topics"][0]
    
                if isinstance(log, AttributeDict):
                    # The following code is not going to work, because AttributeDict magic
                    raise RuntimeError("web3.py AttributeDict middleware detected. Please remove it with web3.middleware_onion.remove('attrdict') or from web3.provider.middleware list before attempting to read events")
    
                if isinstance(log["data"], HexBytes):
                    raise RuntimeError("web3.py pythonic middleware detected. Please remove it with web3.middleware_onion.remove('pythonic') before attempting to read events")
    
                log["context"] = context
    
                if type(event_signature) == HexBytes:
                    # Make sure we use lowercase string notation everywhere
                    event_signature = event_signature.hex()
    
                log["event"] = filter.topics[event_signature]
    
                # Can be hex string or integer (EthereumTester)
                log["blockNumber"] = convert.convert_jsonrpc_value_to_int(log["blockNumber"])
    
                # Used for debugging if we are getting bad data from node
                # or internally confused
                log["chunk_id"] = start_block
    
                if reorg_mon:
                    # Raises exception if chain tip has changed
                    timestamp = reorg_mon.check_block_reorg(block_number, block_hash)
                    assert timestamp is not None, f"Timestamp missing for block number {block_number}, hash {block_hash}. reorg known last block is: {reorg_mon.get_last_block_read()}"
                    log["timestamp"] = timestamp
                else:
                    if timestamps is not None:
                        try:
                            log["timestamp"] = timestamps[block_hash]
                            if type(log["timestamp"]) not in (int, float):
                                raise BadTimestampValueReturned(f"Timestamp was not int or float: {type(log['timestamp'])}: {type(log['timestamp'])}")
                        except KeyError as e:
                            # Reorg mon would handle this natively
                            raise TimestampNotFound(f"EVM event reader cannot match timestamp.\n" f"Timestamp missing for block number {block_number:,}, hash {block_hash}.\n" f" our timestamp table has {len(timestamps)} blocks.") from e
                    else:
                        # Not set, because reorg mon and timestamp extractor not provided,
                        # the caller must do the timestamp resolution themselves
                        log["timestamp"] = None
    
                yield log
    
    

    def prepare_filter(self, events: List[ContractEvent]) -> Filter:
        """Creates internal filter to match contract events."""
    
        # Construct our bloom filter
        bloom = BloomFilter()
        topics = {}
    
        for event in events:
            signatures = event.build_filter().topics
    
            for signature in signatures:
                topics[signature] = event
                # TODO: Confirm correct usage of bloom filter for topics
                bloom.add(bytes.fromhex(signature[2:]))
    
        filter = Filter(topics, bloom)
    
        return filter

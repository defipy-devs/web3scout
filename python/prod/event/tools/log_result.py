from web3.contract.contract import ContractEvent
from typing import TypedDict, Optional, List
from .log_context import LogContext

class LogResult(TypedDict):
    """One emitted Solidity event.

    - Type mappings for a raw Python :py:class:`dict` object

    - Designed for high performance at the cost of readability and usability

    - The values are untranslated hex strings to maximize the reading speed of events

    - See :py:func:`decode_event` how to turn to ABI converted data

    - See :py:mod:`eth_defi.event_reader.reader` for more information

    Example data (PancakeSwap swap):

    .. code-block:: text

        {
            'address': '0xc91cd2b9c9aafe494cf3ccc8bee7795deb17231a',
            'blockHash': '0x3bc60abea8fca30516f48b0374542b9c8fa554061c8802d7bcd4211fffbf6caf',
            'blockNumber': 30237147,
            'chunk_id': 30237147,
            'context': None,
            'data': '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000de90d34e1f2e65c0000000000000000000000000000000000000000000018e627902bfb974416f90000000000000000000000000000000000000000000000000000000000000000',
            'event': <class 'web3._utils.datatypes.Swap'>,
            'logIndex': '0x3',
            'removed': False,
            'timestamp': 1690184818,
            'topics': ['0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822',
                    '0x00000000000000000000000064c425b6fa04873ea460cda049b340d79cf859d7',
                    '0x000000000000000000000000ad1fedfb04377c4b849cef6ef9627bca41955fa0'],
            'transactionHash': '0xf2287653559f01d8afba9ae00386d453b731699b784851f7a8504d41dee7503b',
            'transactionIndex': '0x1'
        }

    """

    #: User passed context for the event reader
    context: LogContext

    #: Contract event matches for this raw log
    #:
    #: To use web3.py helpers to decode this log.
    #:
    #: This event instance is just a class reference and does
    #: not contain any bound data.
    #:
    event: ContractEvent

    #: Smart contract address
    address: str

    #: Block where the event was
    blockHash: str

    #: Block number as hex string
    blockNumber: str

    #: UNIX timestamp of the block number.
    #: Synthesized by block reader code, not present in the receipt.
    #: May be None if timestamp fetching is disabled for the speed reasons.
    timestamp: Optional[int]

    #: Transaction where the event occred
    transactionHash: str

    #: Log index as a hex number
    logIndex: str

    #: Topics in this receipt.
    #: `topics[0]` is always the event signature.
    #:
    #: TODO: Whether these are strings or HexBytes depends on the EVM backend and Web3 version.
    #: Resolve this so that results are normalised to one type.
    #:
    #: See :py:mod:`eth_defi.reader.conversion` how to get Python values out of this.
    #:
    topics: List[str]

    #: Block reorg helper
    removed: bool

    #: Data related to the event
    #:
    #: As raw hex dump from the JSON-RPC.
    #:
    #: See :py:func:`eth_defi.reader.conversion.decode_data` to split to args.
    #:
    data: str
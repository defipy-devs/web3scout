from typing import Optional, Protocol
from ..event.tools.log_context import LogContext

# For typing.Protocol see https://stackoverflow.com/questions/68472236/type-hint-for-callable-that-takes-kwargs
class ProgressUpdate(Protocol):
    """Informs any listener about the state of an event scan.

    Called before a new block is processed.

    Hook this up with `tqdm` for an interactive progress bar.
    """

    def __call__(
        self,
        current_block: int,
        start_block: int,
        end_block: int,
        chunk_size: int,
        total_events: int,
        last_timestamp: Optional[int],
        context: LogContext,
    ):
        """
        :param current_block:
            The block we are about to scan.
            After this scan, we have scanned `current_block + chunk_size` blocks

        :param start_block:
            The first block in our total scan range.

        :param end_block:
            The last block in our total scan range.

        :param chunk_size:
            What was the chunk size (can differ for the last scanned chunk)

        :param total_events:
            Total events picked up so far

        :param last_timestamp:
            UNIX timestamp of last picked up event (if any events picked up)

        :param context:
            Current context
        """
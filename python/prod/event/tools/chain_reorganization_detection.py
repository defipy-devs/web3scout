

class ChainReorganizationDetected(Exception):
    block_number: int
    original_hash: str
    new_hash: str

    def __init__(self, block_number: int, original_hash: str, new_hash: str):
        self.block_number = block_number
        self.original_hash = original_hash
        self.new_hash = new_hash

        super().__init__(f"Block reorg detected at #{block_number:,}. Original hash: {original_hash}. New hash: {new_hash}")
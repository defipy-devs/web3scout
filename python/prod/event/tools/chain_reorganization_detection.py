# This file contains code adapted from web3-ethereum-defi (https://github.com/Kartograf/web3-ethereum-defi)
# Licensed under the MIT License.
# Original copyright (c) 2023 Kartograf contributors.

# Additional modifications by Ian Moore, 2023–2025
# Licensed under the Apache License, Version 2.0

class ChainReorganizationDetected(Exception):
    block_number: int
    original_hash: str
    new_hash: str

    def __init__(self, block_number: int, original_hash: str, new_hash: str):
        self.block_number = block_number
        self.original_hash = original_hash
        self.new_hash = new_hash

        super().__init__(f"Block reorg detected at #{block_number:,}. Original hash: {original_hash}. New hash: {new_hash}")
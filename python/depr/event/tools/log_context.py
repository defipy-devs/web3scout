# This file contains code adapted from web3-ethereum-defi (https://github.com/Kartograf/web3-ethereum-defi)
# Licensed under the MIT License.
# Original copyright (c) 2023 Kartograf contributors.

# Additional modifications by Ian Moore, 2023–2025
# Licensed under the Apache License, Version 2.0

class LogContext:
    """An abstract context class you can pass around for the log results.

    Subclass this and add your own data / methods.

    See `scripts/read-uniswap-v2-pairs-and-swaps.py` for an example.
    """
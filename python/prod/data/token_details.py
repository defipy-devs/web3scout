from typing import Optional
from decimal import Decimal
from dataclasses import dataclass
from functools import cached_property
from web3.contract import Contract
from eth_typing import HexAddress

@dataclass
class TokenDetails:
    """ERC-20 token Python presentation.

    - A helper class to work with ERC-20 tokens.

    - Read on-chain data, deal with token value decimal conversions.

    - Any field can be ``None`` for non-well-formed tokens.

    Example how to get USDC details on Polygon:

    .. code-block:: python

        usdc = fetch_erc20_details(web3, "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")  # USDC on Polygon
        formatted = f"Token {usdc.name} ({usdc.symbol}) at {usdc.address} on chain {usdc.chain_id}"
        assert formatted == "Token USD Coin (PoS) (USDC) at 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 on chain 137"
    """

    #: The underlying ERC-20 contract proxy class instance
    contract: Contract

    #: Token name e.g. ``USD Circle``
    name: Optional[str] = None

    #: Token symbol e.g. ``USDC``
    symbol: Optional[str] = None

    #: Token supply as raw units
    total_supply: Optional[int] = None

    #: Number of decimals
    decimals: Optional[int] = None

    def __eq__(self, other):
        """Token is the same if it's on the same chain and has the same contract address."""
        assert isinstance(other, TokenDetails)
        return (self.contract.address == other.contract.address) and (self.chain_id == other.chain_id)

    def __hash__(self):
        """Token hash."""
        return hash((self.chain_id, self.contract.address))

    def __repr__(self):
        return f"<{self.name} ({self.symbol}) at {self.contract.address}, {self.decimals} decimals, on chain {self.chain_id}>"

    @cached_property
    def chain_id(self) -> int:
        """The EVM chain id where this token lives."""
        return self.contract.w3.eth.chain_id

    @property
    def address(self) -> HexAddress:
        """The address of this token."""
        return self.contract.address

    def convert_to_decimals(self, raw_amount: int) -> Decimal:
        """Convert raw token units to decimals.

        Example:

        .. code-block:: python

            details = fetch_erc20_details(web3, token_address)
            # Convert 1 wei units to edcimals
            assert details.convert_to_decimals(1) == Decimal("0.0000000000000001")

        """
        return Decimal(raw_amount) / Decimal(10**self.decimals)

    def convert_to_raw(self, decimal_amount: Decimal) -> int:
        """Convert decimalised token amount to raw uint256.

        Example:

        .. code-block:: python

            details = fetch_erc20_details(web3, token_address)
            # Convert 1.0 USDC to raw unit with 6 decimals
            assert details.convert_to_raw(1) == 1_000_000

        """
        return int(decimal_amount * 10**self.decimals)

    def fetch_balance_of(self, address: HexAddress | str, block_identifier="latest") -> Decimal:
        """Get an address token balance.

        :param block_identifier:
            A specific block to query if doing archive node historical queries

        :return:
            Converted to decimal using :py:meth:`convert_to_decimal`
        """
        raw_amount = self.contract.functions.balanceOf(address).call(block_identifier=block_identifier)
        return self.convert_to_decimals(raw_amount)

    @staticmethod
    def generate_cache_key(chain_id: int, address: str) -> int:
        """Generate a cache key for this token.

        - Cached by (chain, address) tuple

        - Validate the inputs before generating the key
        """
        assert type(chain_id) == int
        assert type(address) == str
        assert address.startswith("0x")
        return hash((chain_id, address.lower()))
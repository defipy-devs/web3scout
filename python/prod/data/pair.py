"""Uniswap v2 pair info.

- See :py:class:`PairDetails` for a helper class
  to get price and other data from the trading pairs of :Uniswap v2 like DEXes
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union, Optional

from eth_typing import HexAddress
from web3.contract import Contract

from ..abi.abi_load import ABILoad
from ..data.token_details import TokenDetails
from ..token.token import Token


@dataclass(frozen=True, slots=True)
class PairDetails:
    """Uniswap v2 trading pair info.

    An example usage how to get the latest price of a pair on PancakeSwap.
    The `PairDetails` class will do an automatic conversion of prices to human-readable, decimal format:

    .. code-block:: python

        from web3 import Web3, HTTPProvider

        from eth_defi.chain import install_chain_middleware
        from eth_defi.uniswap_v2.pair import fetch_pair_details

        web3 = Web3(HTTPProvider("https://bsc-dataseed.bnbchain.org"))

        print(f"Connected to chain {web3.eth.chain_id}")

        # BNB Chain does its own things
        install_chain_middleware(web3)

        # Find pair addresses on TradingStrategy.ai
        # https://tradingstrategy.ai/trading-view/binance/pancakeswap-v2/bnb-busd
        pair_address = "0x58f876857a02d6762e0101bb5c46a8c1ed44dc16"
        wbnb = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
        busd = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"

        # PancakeSwap has this low level encoded token0/token1 as BNB/BUSD
        # in human-readable token order
        # and we do not need to swap around
        reverse_token_order = False

        pair = fetch_pair_details(
            web3,
            pair_address,
            reverse_token_order,
        )

        assert pair.token0.address == wbnb
        assert pair.token1.address == busd

        price = pair.get_current_mid_price()

        # Assume 1 BUSD = 1 USD
        print(f"The current price of PancakeSwap BNB/BUSD is {price:.4f} USD")

    """

    #: Pool contract
    #:
    #: https://docs.uniswap.org/contracts/v2/reference/smart-contracts/pair#getreserves
    contract: Contract

    #: One pair of tokens
    token0: TokenDetails

    #: One pair of tokens
    token1: TokenDetails

    #: Store the human readable token order on this data.
    #:
    #: If false then pair reads as token0 symbol (WETH) - token1 symbol (USDC).
    #:
    #: If true then pair reads as token1 symbol (USDC) - token0 symbol (WETH).
    reverse_token_order: Optional[bool] = None

    def __eq__(self, other):
        """Implemented for set()"""
        assert isinstance(other, PairDetails)
        return self.address == other.address

    def __hash__(self) -> int:
        """Implemented for set()"""
        return int(self.address, 16)

    def __repr__(self):
        return f"<Pair {self.get_base_token().symbol}-{self.get_quote_token().symbol} at {self.address}>"

    @property
    def address(self) -> HexAddress:
        """Get pair contract address"""
        return self.contract.address

    @property
    def checksum_free_address(self) -> str:
        """Get pair contract address, all lowercase."""
        return self.contract.address.lower()

    def get_base_token(self) -> TokenDetails:
        """Get human-ordered base token."""
        assert self.reverse_token_order is not None, "Reverse token order flag must be check before this operation is possible"
        if self.reverse_token_order:
            return self.token1
        else:
            return self.token0

    def get_quote_token(self) -> TokenDetails:
        """Get human-ordered quote token."""
        assert self.reverse_token_order is not None, "Reverse token order flag must be check before this operation is possible"
        if self.reverse_token_order:
            return self.token0
        else:
            return self.token1

    def convert_price_to_human(self, reserve0: int, reserve1: int, reverse_token_order=None):
        """Convert the price obtained through Sync event

        :param reverse_token_order:
            Decide token order for human (base, quote token) order.
            If set, assume quote token is token0.

            IF set to None, use value from the data.

        """

        if reverse_token_order is None:
            reverse_token_order = self.reverse_token_order

        if reverse_token_order is None:
            reverse_token_order = False

        token0_amount = self.token0.convert_to_decimals(reserve0)
        token1_amount = self.token1.convert_to_decimals(reserve1)

        if reverse_token_order:
            return token0_amount / token1_amount
        else:
            return token1_amount / token0_amount

    def get_current_mid_price(self) -> Decimal:
        """Return the price in this pool.

        Calls `getReserves()` over JSON-RPC and calculate
        the current price basede on the pair reserves.

        See https://docs.uniswap.org/contracts/v2/reference/smart-contracts/pair#getreserves

        :return:
            Quote token / base token price in human digestible form
        """
        assert self.reverse_token_order is not None, "Reverse token order must be set to get the natural price"
        reserve0, reserve1, timestamp = self.contract.functions.getReserves().call()
        return self.convert_price_to_human(reserve0, reserve1, self.reverse_token_order)




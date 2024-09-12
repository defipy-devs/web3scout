"""Raw log event data conversion helpers."""

import cachetools
from web3 import Web3
from typing import Union
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput, ContractLogicError
from eth_typing import HexAddress
from eth_tester.exceptions import TransactionFailed
from ..data.token_details import TokenDetails
from ..abi.abi_load import ABILoad
from ..utils.base_utils import BaseUtils

_call_missing_exceptions = (TransactionFailed, BadFunctionCallOutput, ValueError, ContractLogicError)

DEFAULT_TOKEN_CACHE = cachetools.LRUCache(1024)

class TokenDetailError(Exception):
    """Cannot extract token details for an ERC-20 token for some reason."""

class Token:

    def create_token(
        self,
        web3: Web3,
        deployer: str,
        name: str,
        symbol: str,
        supply: int,
        decimals: int = 18,
    ) -> Contract:
        """Deploys a new ERC-20 token on local dev, testnet or mainnet.
    
        - Uses `ERC20Mock <https://github.com/sushiswap/sushiswap/blob/canary/contracts/mocks/ERC20Mock.sol>`_ contract for the deployment.
    
        - Waits until the transaction has completed
    
        Example:
    
        .. code-block::
    
            # Deploys an ERC-20 token where 100,000 tokens are allocated ato the deployer address
            token = create_token(web3, deployer, "Hentai books token", "HENTAI", 100_000 * 10**18)
            print(f"Deployed token contract address is {token.address}")
            print(f"Deployer account {deployer} has {token.functions.balanceOf(user_1).call() / 10**18} tokens")
    
        Find more examples in :ref:`tutorials` and unit testing source code.
    
        :param web3:
            Web3 instance
    
        :param deployer:
            Deployer account as 0x address.
    
            Make sure this account has enough ETH or native token to cover the gas cost.
    
        :param name: Token name
    
        :param symbol: Token symbol
    
        :param supply: Token starting supply as raw units.
    
            E.g. ``500 * 10**18`` to have 500 tokens minted to the deployer
            at the start.
    
        :param decimals: How many decimals ERC-20 token values have
    
        :return:
            Instance to a deployed Web3 contract.
        """
        return deploy_contract(web3, "ERC20MockDecimals.json", deployer, name, symbol, supply, decimals)
    
    
    def fetch_erc20_details(
        self,
        web3: Web3,
        token_address: Union[HexAddress, str],
        max_str_length: int = 256,
        raise_on_error=True,
        contract_name="ERC20MockDecimals.json",
        cache: cachetools.Cache | None = DEFAULT_TOKEN_CACHE,
        chain_id: int = None,
    ) -> TokenDetails:
        """Read token details from on-chain data.
    
        Connect to Web3 node and do RPC calls to extract the token info.
        We apply some sanitazation for incoming data, like length checks and removal of null bytes.
    
        The function should not raise an exception as long as the underlying node connection does not fail.
    
        Example:
    
        .. code-block:: python
    
            details = fetch_erc20_details(web3, token_address)
            assert details.name == "Hentai books token"
            assert details.decimals == 6
    
        :param web3:
            Web3 instance
    
        :param token_address:
            ERC-20 contract address:
    
        :param max_str_length:
            For input sanitisation
    
        :param raise_on_error:
            If set, raise `TokenDetailError` on any error instead of silently ignoring in and setting details to None.
    
        :param contract_name:
            Contract ABI file to use.
    
            The default is ``ERC20MockDecimals.json``. For USDC use ``centre/FiatToken.json``.
    
        :param cache:
            Use this cache for cache token detail calls.
    
            The main purpose is to easily reduce JSON-RPC API call count.
    
            By default, we use LRU cache of 1024 entries.
    
            Set to ``None`` to disable the cache.
    
            Instance of :py:class:`cachetools.Cache'.
            See `cachetools documentation for details <https://cachetools.readthedocs.io/en/latest/#cachetools.LRUCache>`__.
    
        :param chain_id:
            Chain id hint for the cache.
    
            If not given do ``eth_chainId`` RPC call to figure out.
    
        :return:
            Sanitised token info
        """
    
        if not chain_id:
            chain_id = web3.eth.chain_id
    
        erc_20 = ABILoad().get_deployed_contract(web3, contract_name, token_address)
        key = TokenDetails.generate_cache_key(chain_id, token_address)
    
        if cache is not None:
            cached = cache.get(key)
            if cached is not None:
                return TokenDetails(
                    erc_20,
                    cached["name"],
                    cached["symbol"],
                    cached["supply"],
                    cached["decimals"],
                )
        try:
            symbol = BaseUtils().sanitise_string(erc_20.functions.symbol().call()[0:max_str_length])
        except _call_missing_exceptions as e:
            if raise_on_error:
                raise TokenDetailError(f"Token {token_address} missing symbol") from e
            symbol = None
        except OverflowError:
            # OverflowError: Python int too large to convert to C ssize_t
            # Que?
            # Sai Stablecoin uses bytes32 instead of string for name and symbol information
            # https://etherscan.io/address/0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359#readContract
            symbol = None
    
        try:
            name = BaseUtils().sanitise_string(erc_20.functions.name().call()[0:max_str_length])
        except _call_missing_exceptions as e:
            if raise_on_error:
                raise TokenDetailError(f"Token {token_address} missing name") from e
            name = None
        except OverflowError:
            # OverflowError: Python int too large to convert to C ssize_t
            # Que?
            # Sai Stablecoin uses bytes32 instead of string for name and symbol information
            # https://etherscan.io/address/0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359#readContract
            name = None
    
        try:
            decimals = erc_20.functions.decimals().call()
        except _call_missing_exceptions as e:
            if raise_on_error:
                raise TokenDetailError(f"Token {token_address} missing decimals") from e
            decimals = 0
    
        try:
            supply = erc_20.functions.totalSupply().call()
        except _call_missing_exceptions as e:
            if raise_on_error:
                raise TokenDetailError(f"Token {token_address} missing totalSupply") from e
            supply = None
    
        token_details = TokenDetails(erc_20, name, symbol, supply, decimals)
        if cache is not None:
            cache[key] = {
                "name": name,
                "symbol": symbol,
                "supply": supply,
                "decimals": decimals,
            }
        return token_details
    
    
    def reset_default_token_cache(self):
        """Purge the cached token data.
    
        See :py:data:`DEFAULT_TOKEN_CACHE`
        """
        global DEFAULT_TOKEN_CACHE
        # Cache has a horrible API
        DEFAULT_TOKEN_CACHE.__dict__["_LRUCache__order"] = OrderedDict()
        DEFAULT_TOKEN_CACHE.__dict__["_Cache__currsize"] = 0
        DEFAULT_TOKEN_CACHE.__dict__["_Cache__data"] = dict()
 


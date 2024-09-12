from typing import Union, Optional
from eth_typing import HexAddress
from ..abi.abi_load import ABILoad
from ..data.pair import PairDetails
from ..token.token import Token

class FetchPairDetails:

    def __init__(self):
        pass
    
    def apply(
        self,
        web3,
        pair_contact_address: Union[str, HexAddress],
        reverse_token_order: Optional[bool] = None,
        base_token_address: Optional[str] = None,
        quote_token_address: Optional[str] = None,
    ) -> PairDetails:
        """Get pair info for PancakeSwap, others.
    
        See also :py:class:`PairDetails`.
    
        :param web3:
            Web3 instance
    
        :param pair_contact_address:
            Smart contract address of trading pair
    
        :param reverse_token_order:
            Set the human readable token order.
    
            See :py:class`PairDetails` for more info.
    
        :param base_token_address:
            Automatically determine token order from addresses.
    
        :param quote_token_address:
            Automatically determine token order from addresses.
    
        """
    
        if base_token_address or quote_token_address:
            assert reverse_token_order is None, f"Give either (base_token_address, quote_token_address) or reverse_token_order"
            reverse_token_order = int(base_token_address, 16) > int(quote_token_address, 16)
    
        pool = ABILoading().get_deployed_contract(web3, "sushi/UniswapV2Pair.json", pair_contact_address)
        token0_address = pool.functions.token0().call()
        token1_address = pool.functions.token1().call()
    
        token0 = Token().fetch_erc20_details(web3, token0_address)
        token1 = Token().fetch_erc20_details(web3, token1_address)
    
        return PairDetails(
            pool,
            token0,
            token1,
            reverse_token_order=reverse_token_order,
        )
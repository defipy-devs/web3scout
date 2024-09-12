# Copyright [2024] [Ian Moore]
# Distributed under the MIT License (license terms are at http://opensource.org/licenses/MIT).

from web3 import Web3
from .event import Event
from ..data.filter import Filter
from .tools.conversion import Conversion
from ..token.token import Token
from ..utils.connect import ConnectW3
from ..enums.contracts_enum import JSONContractsEnum as JSONContracts

class CreateEvent(Event):

    def __init__(self, connect_w3: ConnectW3):
        self.__connect_w3 = connect_w3      
                       
    def record(self, event, abi_load):

        event_record = {}
        contract_type = abi_load.get_contract_name()
        
        match contract_type:
            case JSONContracts.IUniswapV2Pair:
                event_record = self._uni_v2_record(event, abi_load)
            case JSONContracts.UniswapV2Pair:
                event_record = self._uni_v2_record(event, abi_load)                
            case JSONContracts.UniswapV3Factory:
                event_record = self._uni_v3_record(event, abi_load)                
           
        return event_record

    def _uni_v2_record(self, event, abi_load):

        return {}   
    
    def _uni_v3_record(self, event, abi_load):

        chain_nm = self.__connect_w3.get_chain_name()
        contract_nm = abi_load.get_contract_name()
        platform_nm = abi_load.get_platform_name()        

        event_signature, token0, token1, fee = event["topics"]
        args = Conversion().decode_data(event["data"])
        w3 = self.__connect_w3.get_w3()
    
        token0_address = Conversion().convert_uint256_string_to_address(token0)
        token1_address = Conversion().convert_uint256_string_to_address(token1)
        token0 = Token().fetch_erc20_details(w3, token0_address, raise_on_error=False)
        token1 = Token().fetch_erc20_details(w3, token1_address, raise_on_error=False)
        
        event_record = {}
        event_record['chain'] = chain_nm
        event_record['contract'] = contract_nm.lower()
        event_record['type'] = event["event"].event_name.lower()
        event_record['platform'] = platform_nm
        event_record['address'] = event["address"]
        event_record['tx_hash'] = event["transactionHash"]
        event_record['blk_num'] = event["blockNumber"]
        event_record['timestamp'] = event["timestamp"]
        event_record['details'] = {}
        event_record['details']['web3_type'] = event["event"]
        event_record['details']['token0'] = token0_address
        event_record['details']['token1'] = token1_address
        event_record['details']['token0_symbol'] = token0.symbol
        event_record['details']['token1_symbol'] = token1.symbol  
        event_record['details']['fee'] = Conversion().convert_uint256_string_to_int(fee)         

        return event_record   
    

 
     
    def filter(self, contract, addr = None):
        return Filter.create_filter(address=addr, event_types=[contract.events.PoolCreated])
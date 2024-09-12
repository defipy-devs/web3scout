# Copyright [2024] [Ian Moore]
# Distributed under the MIT License (license terms are at http://opensource.org/licenses/MIT).

from web3 import Web3
from .event import Event
from ..data.filter import Filter
from .tools.conversion import Conversion
from ..utils.connect import ConnectW3
from ..enums.contracts_enum import JSONContractsEnum as JSONContracts

class SwapEvent(Event):

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
            case JSONContracts.UniswapV3Pool:
                event_record = self._uni_v3_record(event, abi_load)                
           
        return event_record     
                        
    def _uni_v2_record(self, event, abi_load):

        topics = event["topics"]
        arguments = Conversion().decode_data(event["data"])

        chain_nm = self.__connect_w3.get_chain_name()
        contract_nm = abi_load.get_contract_name()
        platform_nm = abi_load.get_platform_name()        
    
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
        event_record['details']['token0'] = Conversion().convert_uint256_hex_string_to_address(topics[1])
        event_record['details']['token1'] = Conversion().convert_uint256_hex_string_to_address(topics[2])
        event_record['details']['amount0In'] = Conversion().convert_int256_bytes_to_int(arguments[0]) 
        event_record['details']['amount1Out'] = Conversion().convert_int256_bytes_to_int(arguments[3]) 

        return event_record

    def _uni_v3_record(self, event, abi_load):

        topics = event["topics"]
        args  = Conversion().decode_data(event["data"])
        token0_address = Conversion().convert_uint256_hex_string_to_address(topics[1])
        token1_address = Conversion().convert_uint256_hex_string_to_address(topics[2])

        chain_nm = self.__connect_w3.get_chain_name()
        contract_nm = abi_load.get_contract_name()
        platform_nm = abi_load.get_platform_name()                
    
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
        if(len(args) == 5):
            event_record['details']['amount0'] = Conversion().convert_int256_bytes_to_int(args[0], signed=self._direction(args[0])) 
            event_record['details']['amount1'] = Conversion().convert_int256_bytes_to_int(args[1], signed=self._direction(args[1])) 
            event_record['details']['sqrt_price_x96'] = Conversion().convert_int256_bytes_to_int(args[2]) 
            event_record['details']['liquidity'] = Conversion().convert_int256_bytes_to_int(args[3]) 
            event_record['details']['tick'] = Conversion().convert_int256_bytes_to_int(args[4], signed=self._direction(args[4])) 

        return event_record 

    def _direction(self, val):
        val1 = Conversion().convert_int256_bytes_to_int(val, signed=False) 
        val2 = Conversion().convert_int256_bytes_to_int(val, signed=True)
        return val1 != val2        
     
    def filter(self, contract, addr = None):
        return Filter.create_filter(address=addr, event_types=[contract.events.Swap])
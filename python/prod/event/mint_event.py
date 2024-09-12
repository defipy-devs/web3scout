# Copyright [2024] [Ian Moore]
# Distributed under the MIT License (license terms are at http://opensource.org/licenses/MIT).

from web3 import Web3
from .event import Event
from ..data.filter import Filter
from .tools.conversion import Conversion
from ..utils.connect import ConnectW3
from ..enums.contracts_enum import JSONContractsEnum as JSONContracts
import math

class MintEvent(Event):

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

        chain_nm = self.__connect_w3.get_chain_name()
        contract_nm = abi_load.get_contract_name()
        platform_nm = abi_load.get_platform_name()

        topics = event["topics"]
        arguments = Conversion().decode_data(event["data"])        
                
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
        event_record['details']['token0'] = Conversion().convert_uint256_hex_string_to_address(topics[0])
        event_record['details']['token1'] = Conversion().convert_uint256_hex_string_to_address(topics[1])

        if(len(arguments) == 1):
            event_record['details']['amount0In'] = Conversion().convert_int256_bytes_to_int(arguments[0]) 
            event_record['details']['amount1Out'] = math.nan 
        elif(len(arguments) >= 1):
            event_record['details']['amount0In'] = Conversion().convert_int256_bytes_to_int(arguments[0]) 
            event_record['details']['amount1Out'] = Conversion().convert_int256_bytes_to_int(arguments[1])  


        return event_record   


    def _uni_v3_record(self, event, abi_load):

        chain_nm = self.__connect_w3.get_chain_name()
        contract_nm = abi_load.get_contract_name()
        platform_nm = abi_load.get_platform_name()

        event_signature, owner, tick_lower, tick_upper = event["topics"]
        sender, liquidity_amount, amount0, amount1  = Conversion().decode_data(event["data"])
        arguments = Conversion().decode_data(event["data"])            

        event_record = {}
        event_record['chain'] = chain_nm
        event_record['contract'] = contract_nm.lower()
        event_record['type'] = event["event"].event_name.lower()
        event_record['platform'] = platform_nm
        event_record['pool_address'] = event["address"]
        event_record['tx_hash'] = event["transactionHash"]
        event_record['blk_num'] = event["blockNumber"]
        event_record['timestamp'] = event["timestamp"]
        event_record['details'] = {}
        event_record['details']['web3_type'] = event["event"]
        event_record['details']['owner'] = Conversion().convert_uint256_hex_string_to_address(owner)
        event_record['details']['tick_lower'] = Conversion().convert_uint256_string_to_int(tick_lower, signed=True)
        event_record['details']['tick_upper'] = Conversion().convert_uint256_string_to_int(tick_upper, signed=True)  
        if(len(arguments) == 4):
            event_record['details']['liquidity_amount'] = Conversion().convert_int256_bytes_to_int(arguments[1])
            event_record['details']['amount0'] = Conversion().convert_int256_bytes_to_int(arguments[2])
            event_record['details']['amount1'] = Conversion().convert_int256_bytes_to_int(arguments[3])

        return event_record   
    
    def filter(self, contract, addr = None):
        return Filter.create_filter(address=addr, event_types=[contract.events.Mint])
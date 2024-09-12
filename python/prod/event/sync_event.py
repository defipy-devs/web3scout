# Copyright [2024] [Ian Moore]
# Distributed under the MIT License (license terms are at http://opensource.org/licenses/MIT).

from web3 import Web3
from .event import Event
from .tools.conversion import Conversion
from ..uniswap_v2.fetch_pair_details import FetchPairDetails
from ..data.filter import Filter
from ..utils.connect import ConnectW3
from ..enums.contracts_enum import JSONContractsEnum as JSONContracts


class SyncEvent(Event):

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

        w3 = self.__connect_w3.get_w3()
        pair: PairDetails = FetchPairDetails().apply(w3, event['address'])
    
        amt0 = Conversion().convert_int256_bytes_to_int(arguments[0]) 
        amt1 = Conversion().convert_int256_bytes_to_int(arguments[1])  
        amt0_human = amt0/(10**pair.token0.decimals)
        amt1_human = amt1/(10**pair.token1.decimals)    
    
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
        event_record['details']['web3_type'] = event['event']
        event_record['details']['token0'] = pair.token0.address
        event_record['details']['token1'] = pair.token1.address
        event_record['details']['token0_symbol'] = pair.token0.symbol
        event_record['details']['token1_symbol'] = pair.token1.symbol 
        event_record['details']['token0_decimal'] = pair.token0.decimals
        event_record['details']['token1_decimal'] = pair.token1.decimals        
        event_record['details']['amount0'] = amt0
        event_record['details']['amount1'] = amt1
        event_record['details']['price'] = amt1_human/amt0_human

        return event_record

    def _uni_v3_record(self, event, abi_load):

        event_record = {}

        return event_record     
     
    def filter(self, contract, addr = None):
        return Filter.create_filter(address=addr, event_types=[contract.events.Sync])
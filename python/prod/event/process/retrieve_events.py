# This file contains code adapted from web3-ethereum-defi (https://github.com/Kartograf/web3-ethereum-defi)
# Licensed under the MIT License.
# Original copyright (c) 2023 Kartograf contributors.

# Additional modifications by Ian Moore, 2023–2025
# Licensed under the Apache License, Version 2.0


from ...abi.abi_load import ABILoad
from ...enums.init_event_enum import InitEventEnum as InitEvent
from ...utils.connect import ConnectW3
from ..event import Event
from ..tools.log_result import LogResult
from ..tools.conversion import Conversion
from ..tools.rpc_reorganization_monitor import JSONRPCReorganizationMonitor
from .read_events import ReadEvents
import pandas as pd

class RetrieveEvents:

    def __init__(self, connect: ConnectW3, abi: ABILoad, verbose = True):
        self.__connect = connect   
        self.__abi = abi 
        self.__w3 = self.__connect.get_w3()
        self.__contract = None
        self.__verbose = verbose
        self.__w3.middleware_onion.clear()
    
    def apply(self, event_type, address = None, start_block = None, end_block = None, argument_filters = None):

        # The w3 handle is built by ConnectW3.apply() at construction time, so
        # don't re-ping the node on every apply() -- that extra round-trip flakes
        # under provider rate-limiting. A genuinely unreachable node surfaces as a
        # clear error from the get_logs read below.
        assert self.__w3 is not None, 'WEB3SCOUT Event Reader: NOT_CONNECTED'
        assert address != None, 'WEB3SCOUT Event Reader: NO_ADDRESS'

        self.__contract = self.retrieve_contract(address)
        event = InitEvent().apply(self.__connect, event_type)
        read_events = self.gen_read_events(event, start_block, end_block, argument_filters)
        return self.to_dict(read_events)

    def get_contract(self):
        return self.__contract

    def to_dict(self, read_events = {}):
        
        dict_events = {}
        for k, evt in enumerate(read_events):
            evt_record = self.reorg_event_record(evt)
            dict_events[k] = evt_record
        return dict_events    
    
    def to_dataframe(self, dict_events):
        return pd.DataFrame.from_dict(dict_events, orient='index')

    def gen_read_events(self, event, start_block = None, end_block = None, argument_filters = None):
        s_block = 1 if start_block == None else start_block
        e_block = self.latest_block() if end_block == None else end_block
        # event.filter() returns decoded logs via stateless eth_getLogs, which
        # works on load-balanced public RPCs (unlike stateful eth_newFilter).
        if argument_filters is not None:
            read_events = event.filter(self.__contract, fromBlock=s_block, toBlock=e_block, argument_filters=argument_filters)
        else:
            read_events = event.filter(self.__contract, fromBlock=s_block, toBlock=e_block)
        return read_events

    def reorg_event_record(self,evt):
        event_fields = ['blockNumber','event','address','blockHash','logIndex','transactionHash','transactionIndex','args']
        event_record = {}
        for field in event_fields:

            if(field == 'blockHash' or field == 'transactionHash'):
                event_record[field] = Conversion().convert_hex_bytes_to_string(evt[field])
            else:
                event_record[field] = evt[field]
                
        return event_record

    def retrieve_contract(self, address):
        chksum_addr = address if address == None else self.__w3.to_checksum_address(address)
        return self.__abi.apply(self.__w3, chksum_addr)
    
    def latest_block(self):
        reorg_mon = JSONRPCReorganizationMonitor(self.__w3, check_depth=3)
        reorg_mon.load_initial_block_headers(block_count=5)
        return reorg_mon.get_last_block_live()
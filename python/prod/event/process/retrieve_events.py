from ...abi.abi_load import ABILoad
from ...enums.init_event_enum import InitEventEnum as InitEvent
from ...utils.connect import ConnectW3
from ..event import Event
from ..tools.log_result import LogResult
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
    
    def apply(self, event_type, address = None, start_block = None, end_block = None):

        assert self.__connect.is_connect(), 'PACHIRA Event Reader: NOT_CONNECTED'
        
        self.__contract = self.retrieve_contract(address)
        event = InitEvent().apply(self.__connect, event_type)
        read_events = self.gen_read_events(event, start_block, end_block)
        processed_events = set()
        dict_events = {}
        evt: LogResult
        for k, evt in enumerate(read_events):
            key = evt["blockHash"] + evt["transactionHash"] + evt["logIndex"]    
            record_event = event.record(evt, self.__abi)
               
            dict_events[k] = record_event
            if key not in processed_events:
                if(self.__verbose): print(f"{event_type} at block:{evt['blockNumber']:,} tx:{evt['transactionHash']}")
                processed_events.add(key)
        else:
            if(self.__verbose): print(".")

        return dict_events 

    def get_contract(self):
        return self.__contract
    
    def to_dataframe(self, dict_events):
        return pd.DataFrame.from_dict(dict_events, orient='index')

    def gen_read_events(self, event, start_block = None, end_block = None):
        s_block = 1 if start_block == None else start_block
        e_block = self.latest_block() if end_block == None else end_block
        event_filt = event.filter(self.__contract)
        read_events = ReadEvents().apply(self.__w3, start_block=s_block, end_block=e_block, filter=event_filt)   
        return read_events

    def retrieve_contract(self, address):
        return self.__abi.apply(self.__w3, address)
    
    def latest_block(self):
        reorg_mon = JSONRPCReorganizationMonitor(self.__w3, check_depth=3)
        reorg_mon.load_initial_block_headers(block_count=5)
        return reorg_mon.get_last_block_live()
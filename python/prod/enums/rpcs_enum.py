from dataclasses import dataclass
from .nets_enum import NetsEnum

DEFAULT_NET = NetsEnum.POLYGON

class RPCEnum:
    
    def get_key(net = DEFAULT_NET):
        match net:
            case NetsEnum.POLYGON:
                select_key = 'JSON_RPC_POLYGON'
            case NetsEnum.LOCALHOST:
                select_key = 'JSON_RPC_LOCALHOST'                
           
        return select_key 

    def get_rpc(net = DEFAULT_NET):
        match net:
            case NetsEnum.POLYGON:
                select_rpc = 'https://polygon-rpc.com'
            case NetsEnum.LOCALHOST:
                select_rpc = 'http://127.0.0.1:8545'                
           
        return select_rpc 
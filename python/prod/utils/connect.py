# This file contains code adapted from web3-ethereum-defi (https://github.com/Kartograf/web3-ethereum-defi)
# Licensed under the MIT License.
# Original copyright (c) 2023 Kartograf contributors.

# Additional modifications by Ian Moore, 2023–2025
# Licensed under the Apache License, Version 2.0

from web3 import Web3
from ..enums.nets_enum import NetsEnum
from ..enums.rpcs_enum import RPCEnum

DEFAULT_CHAIN = NetsEnum.LOCALHOST

class ConnectW3():

    def __init__(self, chain = None):        
        self.__chain = DEFAULT_CHAIN if chain == None else chain
        self.__w3 = None
     
    def apply(self):
        rpc = RPCEnum.get_rpc(self.__chain) 
        self.__w3 = Web3(Web3.HTTPProvider(rpc))

    def is_connect(self):
        return self.__w3.is_connected() if self.__w3 != None else False

    def get_w3(self):
        return self.__w3

    def get_chain_name(self):
        return self.__chain
# Copyright 2023–2025 Ian Moore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
            case _: 
                select_rpc = net 
           
        return select_rpc 
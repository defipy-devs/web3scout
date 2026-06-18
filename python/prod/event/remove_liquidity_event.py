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

from web3 import Web3
from .event import Event
from ..utils.connect import ConnectW3

class RemoveLiquidityEvent(Event):

    def __init__(self, connect_w3: ConnectW3):
        self.__connect_w3 = connect_w3

    def record(self, event, abi_load):
        # Not wired into RetrieveEvents.apply() — the generic reorg_event_record
        # path serves liquidity events (decision #1). Stub satisfies the ABC.
        return {}

    def filter(self, contract, addr = None, fromBlock = None, toBlock = None, argument_filters = None):
        if argument_filters:
            return contract.events.RemoveLiquidity.create_filter(fromBlock = fromBlock, toBlock = toBlock, argument_filters = argument_filters)
        return contract.events.RemoveLiquidity.create_filter(fromBlock = fromBlock, toBlock = toBlock)

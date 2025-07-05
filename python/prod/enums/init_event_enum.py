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
from .event_type_enum import EventTypeEnum as EventType
from ..event.mint_event import MintEvent
from ..event.swap_event import SwapEvent
from ..event.burn_event import BurnEvent
from ..event.create_event import CreateEvent
from ..event.transfer_event import TransferEvent
from ..event.sync_event import SyncEvent

DEFAULT_EVENT = EventType.MINT

class InitEventEnum:
    
    def apply(self, connect, event_type = DEFAULT_EVENT):
        match event_type:
            case EventType.MINT:
                event = MintEvent(connect)
            case EventType.SWAP:
                event = SwapEvent(connect)     
            case EventType.BURN:
                event = BurnEvent(connect)         
            case EventType.SYNC:
                event = SyncEvent(connect)      
            case EventType.TRANSFER:
                event = TransferEvent(connect)     
            case EventType.CREATE:
                event = CreateEvent(connect)                    
                           
           
        return event 
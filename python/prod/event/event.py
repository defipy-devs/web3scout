# Copyright [2024] [Ian Moore]
# Distributed under the MIT License (license terms are at http://opensource.org/licenses/MIT).

from abc import *

class Event(ABC):
             
    @abstractmethod        
    def record(self, event, abi_load):
        pass

    @abstractmethod        
    def filter(self, contract):
        pass


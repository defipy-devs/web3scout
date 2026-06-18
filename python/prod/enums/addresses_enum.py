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

@dataclass(frozen=True)
class AddressesEnum:

    # Balancer V2 Vault — deterministic singleton, same address on every
    # chain Balancer V2 is deployed to (Ethereum, Polygon, Arbitrum, …).
    BALANCER_V2_VAULT: str = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"

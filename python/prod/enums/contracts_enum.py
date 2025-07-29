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
class JSONContractsEnum:
    ERC20: str = "ERC20MockDecimals"
    IUniswapV2Pair: str = "IUniswapV2Pair"
    UniswapV2Pair: str = "UniswapV2Pair"
    UniswapV2Router02: str = "UniswapV2Router02"
    UniswapV2Factory: str = "UniswapV2Factory"
    UniswapV3Pool: str = "UniswapV3Pool"
    UniswapV3Factory: str = "UniswapV3Factory"
    UniV2IndexedYieldLinearExitPool: str = "UniV2IndexedYieldLinearExitPool"
    MintableRCIndexedYieldLinearExitPoolStudy: str = "MintableRCIndexedYieldLinearExitPoolStudy"




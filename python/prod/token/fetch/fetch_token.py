# ─────────────────────────────────────────────────────────────────────────────
# Apache 2.0 License (DeFiPy)
# ─────────────────────────────────────────────────────────────────────────────
# Copyright 2023–2025 Ian Moore
# Email: defipy.devs@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from web3 import Web3
from uniswappy.erc import ERC20
from ...abi.abi_load import ABILoad
from ...enums.platforms_enum import PlatformsEnum
from ...enums.contracts_enum import JSONContractsEnum

class FetchToken:
    
    def __init__(self, w3):
        self.w3 = w3

    def apply(self, token_address):
        name = self.get_token_symbol(token_address)
        decimal = self.get_token_decimals(token_address)
        return ERC20(name, token_address, decimal)

    def amt_to_decimal(self, tkn, amt):
        return amt/(10**tkn.token_decimal)
        
    def get_erc20_abi(self, token_address):
        abi_obj = ABILoad(PlatformsEnum.ERC, JSONContractsEnum.ERC20)  # Load ABI here  
        contract_instance = abi_obj.apply(self.w3, token_address)
        return contract_instance.abi
        
    def get_token_symbol(self, token_address):
        """Fetch the token symbol for a given ERC-20 token address."""
        # Minimal ERC-20 ABI for symbol()
        erc20_abi = self.get_erc20_abi(token_address)
        try:
            # Ensure address is checksummed
            checksum_address = self.w3.to_checksum_address(token_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
            symbol = contract.functions.symbol().call()
            return symbol
        except Exception as e:
            print(f"Error fetching symbol for {token_address}: {e}")
            return None

    def get_token_name(self, token_address):
        """Fetch the token symbol for a given ERC-20 token address."""
        # Minimal ERC-20 ABI for symbol()
        erc20_abi = self.get_erc20_abi(token_address)
        try:
            # Ensure address is checksummed
            checksum_address = self.w3.to_checksum_address(token_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
            name = contract.functions.name().call()
            return name
        except Exception as e:
            print(f"Error fetching symbol for {self.token_address}: {e}")
            return None
    
    def get_token_supply(self, token_address):
        """Fetch the token symbol for a given ERC-20 token address."""
        # Minimal ERC-20 ABI for symbol()
        erc20_abi = self.get_erc20_abi(token_address)
        try:
            # Ensure address is checksummed
            checksum_address = self.w3.to_checksum_address(token_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
            supply = contract.functions.totalSupply().call()
            return supply
        except Exception as e:
            print(f"Error fetching symbol for {self.token_address}: {e}")
            return None
    
    def get_token_decimals(self, token_address):
        """Fetch the number of decimals for a given ERC-20 token address."""
        erc20_abi = self.get_erc20_abi(token_address)
        try:
            checksum_address = self.w3.to_checksum_address(token_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=erc20_abi)
            decimals = contract.functions.decimals().call()
            return decimals
        except Exception as e:
            print(f"Error fetching decimals for {token_address}: {e}")
            return None
    

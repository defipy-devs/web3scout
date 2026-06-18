import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _fn_names(abi_doc):
    return {e["name"] for e in abi_doc["abi"] if e.get("type") == "function"}


class TestBalancerABIs:

    def test_weighted_pool_functions_present(self):
        names = _fn_names(_load_abi("balancer/WeightedPool.json"))
        assert {"getPoolId", "getVault", "getNormalizedWeights",
                "getSwapFeePercentage", "totalSupply"} <= names

    def test_vault_functions_present(self):
        names = _fn_names(_load_abi("balancer/Vault.json"))
        assert "getPoolTokens" in names

    def test_get_pool_tokens_takes_pool_id(self):
        abi = _load_abi("balancer/Vault.json")["abi"]
        fn = next(e for e in abi if e.get("name") == "getPoolTokens")
        assert [i["type"] for i in fn["inputs"]] == ["bytes32"]


class TestBalancerEnums:

    def test_platform_enum_has_balancer(self):
        src = read_source("enums/platforms_enum.py")
        assert 'BALANCER: str = "balancer"' in src

    def test_contract_enum_has_balancer(self):
        src = read_source("enums/contracts_enum.py")
        assert 'BalancerVault: str = "Vault"' in src
        assert 'BalancerWeightedPool: str = "WeightedPool"' in src


class TestBalancerPackaging:

    def test_manifest_includes_balancer_abis(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        assert "python/prod/configs/balancer/Vault.json" in text
        assert "python/prod/configs/balancer/WeightedPool.json" in text

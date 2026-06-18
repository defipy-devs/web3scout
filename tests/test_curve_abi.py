import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _fn(abi_doc, name):
    return next(e for e in abi_doc["abi"]
               if e.get("type") == "function" and e.get("name") == name)


class TestCurveABI:

    def test_functions_present(self):
        abi = _load_abi("curve/StableSwap.json")
        names = {e["name"] for e in abi["abi"] if e.get("type") == "function"}
        assert {"A", "coins", "balances", "fee"} <= names

    def test_coins_index_is_uint256(self):
        abi = _load_abi("curve/StableSwap.json")
        assert [i["type"] for i in _fn(abi, "coins")["inputs"]] == ["uint256"]
        assert [i["type"] for i in _fn(abi, "balances")["inputs"]] == ["uint256"]

    def test_uses_human_A_not_precise(self):
        abi = _load_abi("curve/StableSwap.json")
        names = {e["name"] for e in abi["abi"] if e.get("type") == "function"}
        assert "A" in names
        assert "A_precise" not in names


class TestCurveEnums:

    def test_platform_enum_has_curve(self):
        src = read_source("enums/platforms_enum.py")
        assert 'CURVE: str = "curve"' in src

    def test_contract_enum_has_curve(self):
        src = read_source("enums/contracts_enum.py")
        assert 'CurveStableSwap: str = "StableSwap"' in src


class TestPackagingCloseout:

    def test_manifest_includes_curve_abi(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        assert "python/prod/configs/curve/StableSwap.json" in text

    def test_version_bumped(self):
        setup_py = os.path.join(PROD_PATH, "..", "..", "setup.py")
        with open(setup_py) as f:
            text = f.read()
        assert "version='1.0.0'" in text

    def test_both_protocols_packaged(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        for rel in ("balancer/Vault.json", "balancer/WeightedPool.json",
                    "curve/StableSwap.json"):
            assert "python/prod/configs/" + rel in text

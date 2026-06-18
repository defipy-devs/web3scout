import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _event_names(abi_doc):
    return {e.get("name") for e in abi_doc["abi"] if e.get("type") == "event"}


class TestLiquidityABIs:

    def test_balancer_has_pool_balance_changed(self):
        assert "PoolBalanceChanged" in _event_names(_load_abi("balancer/Vault.json"))

    def test_curve_has_add_and_remove(self):
        names = _event_names(_load_abi("curve/StableSwap.json"))
        assert {"AddLiquidity", "RemoveLiquidity"} <= names

    def test_curve_add_liquidity_3coin_arity(self):
        abi = _load_abi("curve/StableSwap.json")["abi"]
        add = next(e for e in abi if e.get("name") == "AddLiquidity" and e.get("type") == "event")
        ta = next(i for i in add["inputs"] if i["name"] == "token_amounts")
        assert ta["type"] == "uint256[3]"

    def test_remove_liquidity_has_no_invariant(self):
        abi = _load_abi("curve/StableSwap.json")["abi"]
        rem = next(e for e in abi if e.get("name") == "RemoveLiquidity" and e.get("type") == "event")
        assert "invariant" not in {i["name"] for i in rem["inputs"]}


class TestLiquidityEnumsAndWiring:

    def test_event_type_additions(self):
        src = read_source("enums/event_type_enum.py")
        for token in ("POOL_BALANCE_CHANGED", "ADD_LIQUIDITY", "REMOVE_LIQUIDITY"):
            assert token in src

    def test_init_event_maps_new_types(self):
        src = read_source("enums/init_event_enum.py")
        for cls in ("PoolBalanceChangedEvent", "AddLiquidityEvent", "RemoveLiquidityEvent"):
            assert cls in src

    def test_exports(self):
        src = read_source("__init__.py")
        for cls in ("PoolBalanceChangedEvent", "AddLiquidityEvent", "RemoveLiquidityEvent"):
            assert cls in src


class _FakeEvent:
    def __init__(self, name):
        self.name = name
        self.captured = None
    def get_logs(self, **kwargs):
        self.captured = kwargs
        return kwargs

class _FakeEvents:
    def __init__(self, names):
        for n in names:
            setattr(self, n, _FakeEvent(n))

class _FakeContract:
    def __init__(self, event_names):
        self.abi = [{"type": "event", "name": n} for n in event_names]
        self.events = _FakeEvents(event_names)


class TestLiquidityFilterBehavior:

    def test_pool_balance_changed_passes_poolid(self):
        we = pytest.importorskip("web3scout")
        ev = we.PoolBalanceChangedEvent(None)
        c = _FakeContract(["Swap", "PoolBalanceChanged"])
        af = {"poolId": b"\x00" * 32}
        ev.filter(c, fromBlock=1, toBlock=2, argument_filters=af)
        assert c.events.PoolBalanceChanged.captured["argument_filters"] == af

    def test_curve_add_remove_filters(self):
        we = pytest.importorskip("web3scout")
        c = _FakeContract(["TokenExchange", "AddLiquidity", "RemoveLiquidity"])
        we.AddLiquidityEvent(None).filter(c, fromBlock=1, toBlock=2)
        we.RemoveLiquidityEvent(None).filter(c, fromBlock=1, toBlock=2)
        assert c.events.AddLiquidity.captured == {"fromBlock": 1, "toBlock": 2}
        assert c.events.RemoveLiquidity.captured == {"fromBlock": 1, "toBlock": 2}

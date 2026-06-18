import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _event_names(abi_doc):
    return {e.get("name") for e in abi_doc["abi"] if e.get("type") == "event"}


class TestSwapEventABIs:

    def test_balancer_vault_has_swap_event(self):
        assert "Swap" in _event_names(_load_abi("balancer/Vault.json"))

    def test_curve_has_token_exchange_event(self):
        assert "TokenExchange" in _event_names(_load_abi("curve/StableSwap.json"))

    def test_balancer_swap_poolid_indexed(self):
        abi = _load_abi("balancer/Vault.json")["abi"]
        swap = next(e for e in abi if e.get("name") == "Swap" and e.get("type") == "event")
        poolid = next(i for i in swap["inputs"] if i["name"] == "poolId")
        assert poolid["indexed"] is True and poolid["type"] == "bytes32"


class TestVaultAddressConstant:

    def test_addresses_enum_has_vault(self):
        src = read_source("enums/addresses_enum.py")
        assert "BALANCER_V2_VAULT" in src
        assert "0xBA12222222228d8Ba445958a75a0704d566BF2C8" in src

    def test_exported(self):
        src = read_source("__init__.py")
        assert "AddressesEnum as Addr" in src


class TestRetrieveEventsWiring:

    def test_apply_threads_argument_filters(self):
        src = read_source("event/process/retrieve_events.py")
        assert "argument_filters" in src

    def test_swap_filter_branches_on_token_exchange(self):
        src = read_source("event/swap_event.py")
        assert "TokenExchange" in src
        assert "argument_filters" in src


# Real behavior test of the filter branch — no chain needed.
class _FakeEvent:
    def __init__(self, name):
        self.name = name
        self.captured = None
    def create_filter(self, **kwargs):
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


class TestSwapFilterBehavior:

    def _swap_event(self):
        we = pytest.importorskip("web3scout")
        return we.SwapEvent(None)

    def test_uniswap_uses_swap(self):
        se = self._swap_event()
        c = _FakeContract(["Swap", "Mint", "Burn", "Sync"])
        se.filter(c, fromBlock=1, toBlock=2)
        assert c.events.Swap.captured == {"fromBlock": 1, "toBlock": 2}

    def test_curve_uses_token_exchange(self):
        se = self._swap_event()
        c = _FakeContract(["TokenExchange", "AddLiquidity"])
        se.filter(c, fromBlock=1, toBlock=2)
        assert c.events.TokenExchange.captured == {"fromBlock": 1, "toBlock": 2}

    def test_balancer_passes_poolid_filter(self):
        se = self._swap_event()
        c = _FakeContract(["Swap", "PoolBalanceChanged"])
        af = {"poolId": b"\x00" * 32}
        se.filter(c, fromBlock=1, toBlock=2, argument_filters=af)
        assert c.events.Swap.captured["argument_filters"] == af

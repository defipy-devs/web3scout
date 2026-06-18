# Web3Scout — Phase 4: Balancer & Curve Liquidity Events (Claude Code Handoff)

**Status:** Ready for Claude Code (after Phase 3)
**Spec:** `doc/WEB3SCOUT_EVENTS_BALANCER_CURVE_SPEC.md` (decisions locked)
**Phase:** 4 of 4 (Liquidity events)
**Repo:** `web3scout` only
**Prerequisite:** Phase 3 (swap events) merged.

---

## Goal

`apply()` reads liquidity events for both protocols, in the generic `reorg_event_record` shape (decision #1, same as Phase 3):

- **Balancer:** `apply(EventType.POOL_BALANCE_CHANGED, address=Addr.BALANCER_V2_VAULT, argument_filters={'poolId': pid})`. Balancer emits **one** event for both joins and exits — `PoolBalanceChanged` — distinguished by the sign of the `deltas` array (positive = join, negative = exit). There is no separate add/remove event.
- **Curve (3-coin):** `apply(EventType.ADD_LIQUIDITY, address=POOL)` and `apply(EventType.REMOVE_LIQUIDITY, address=POOL)`.

Scope is 3-coin Curve (matching the Phase 2 3pool focus). `RemoveLiquidityOne` / `RemoveLiquidityImbalance` and non-3-coin arities are deferred.

---

## Tasks

### 1. Add liquidity events to the ABIs

**`python/prod/configs/balancer/Vault.json`** — add `PoolBalanceChanged` (dynamic arrays — coin-count-agnostic):

```json
{"anonymous": false, "name": "PoolBalanceChanged", "type": "event", "inputs": [
  {"indexed": true,  "internalType": "bytes32",            "name": "poolId",             "type": "bytes32"},
  {"indexed": true,  "internalType": "address",            "name": "liquidityProvider",  "type": "address"},
  {"indexed": false, "internalType": "contract IERC20[]",  "name": "tokens",             "type": "address[]"},
  {"indexed": false, "internalType": "int256[]",           "name": "deltas",             "type": "int256[]"},
  {"indexed": false, "internalType": "uint256[]",          "name": "protocolFeeAmounts", "type": "uint256[]"}
]}
```

**`python/prod/configs/curve/StableSwap.json`** — add `AddLiquidity` and `RemoveLiquidity`. These carry `uint256[3]` fixed arrays — **3pool-specific**:

```json
{"name": "AddLiquidity", "anonymous": false, "type": "event", "inputs": [
  {"indexed": true,  "name": "provider",      "type": "address"},
  {"indexed": false, "name": "token_amounts", "type": "uint256[3]"},
  {"indexed": false, "name": "fees",          "type": "uint256[3]"},
  {"indexed": false, "name": "invariant",     "type": "uint256"},
  {"indexed": false, "name": "token_supply",  "type": "uint256"}
]}
```

```json
{"name": "RemoveLiquidity", "anonymous": false, "type": "event", "inputs": [
  {"indexed": true,  "name": "provider",      "type": "address"},
  {"indexed": false, "name": "token_amounts", "type": "uint256[3]"},
  {"indexed": false, "name": "fees",          "type": "uint256[3]"},
  {"indexed": false, "name": "token_supply",  "type": "uint256"}
]}
```

**Verify before trusting (critical here):** the `uint256[3]` arity is baked to 3 coins — these decode 3pool but NOT a 2-coin pool. Confirm against the verified 3pool ABI (`0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7`) that: the array sizes are `[3]`, `AddLiquidity` carries `invariant` but `RemoveLiquidity` does **not** (Curve's field sets differ between the two), and the field names/order match. A mismatch here decodes garbage, not nothing. Document in the ABI's surrounding context (or a followups note) that these entries are 3-coin-specific.

No MANIFEST.in change — same filenames.

### 2. EventType enum

`python/prod/enums/event_type_enum.py` — add:

```python
    POOL_BALANCE_CHANGED: str = "pool_balance_changed"
    ADD_LIQUIDITY: str = "add_liquidity"
    REMOVE_LIQUIDITY: str = "remove_liquidity"
```

### 3. New Event subclasses

Three files under `python/prod/event/`. Each implements the `Event` ABC: `filter()` (used) and a `record()` stub (required by the ABC, not wired into `apply()` per decision #1). Match the Apache-2.0 header from the existing event files.

**`python/prod/event/pool_balance_changed_event.py`:**

```python
# Copyright 2023–2025 Ian Moore   (full Apache-2.0 header, verbatim from sibling files)

from web3 import Web3
from .event import Event
from ..utils.connect import ConnectW3

class PoolBalanceChangedEvent(Event):

    def __init__(self, connect_w3: ConnectW3):
        self.__connect_w3 = connect_w3

    def record(self, event, abi_load):
        # Not wired into RetrieveEvents.apply() — the generic reorg_event_record
        # path serves liquidity events (decision #1). Stub satisfies the ABC.
        return {}

    def filter(self, contract, addr = None, fromBlock = None, toBlock = None, argument_filters = None):
        if argument_filters:
            return contract.events.PoolBalanceChanged.create_filter(fromBlock = fromBlock, toBlock = toBlock, argument_filters = argument_filters)
        return contract.events.PoolBalanceChanged.create_filter(fromBlock = fromBlock, toBlock = toBlock)
```

**`python/prod/event/add_liquidity_event.py`** — identical shape, event name `AddLiquidity`:

```python
# (Apache-2.0 header)

from web3 import Web3
from .event import Event
from ..utils.connect import ConnectW3

class AddLiquidityEvent(Event):

    def __init__(self, connect_w3: ConnectW3):
        self.__connect_w3 = connect_w3

    def record(self, event, abi_load):
        return {}

    def filter(self, contract, addr = None, fromBlock = None, toBlock = None, argument_filters = None):
        if argument_filters:
            return contract.events.AddLiquidity.create_filter(fromBlock = fromBlock, toBlock = toBlock, argument_filters = argument_filters)
        return contract.events.AddLiquidity.create_filter(fromBlock = fromBlock, toBlock = toBlock)
```

**`python/prod/event/remove_liquidity_event.py`** — identical, event name `RemoveLiquidity`.

(`argument_filters` is accepted on all three for uniformity; only Balancer's `PoolBalanceChanged` actually uses it — Curve liquidity events are per-pool, so the caller passes none.)

### 4. Wire into `InitEventEnum`

`python/prod/enums/init_event_enum.py` — add imports and `case` arms:

```python
from ..event.pool_balance_changed_event import PoolBalanceChangedEvent
from ..event.add_liquidity_event import AddLiquidityEvent
from ..event.remove_liquidity_event import RemoveLiquidityEvent
```

```python
            case EventType.POOL_BALANCE_CHANGED:
                event = PoolBalanceChangedEvent(connect)
            case EventType.ADD_LIQUIDITY:
                event = AddLiquidityEvent(connect)
            case EventType.REMOVE_LIQUIDITY:
                event = RemoveLiquidityEvent(connect)
```

### 5. Export in package `__init__`

`python/prod/__init__.py` — add alongside the other event imports:

```python
from .event.pool_balance_changed_event import PoolBalanceChangedEvent
from .event.add_liquidity_event import AddLiquidityEvent
from .event.remove_liquidity_event import RemoveLiquidityEvent
```

### 6. Tests

`tests/test_events_liquidity.py` — source-level + filter-branch behavior (reuse the `_FakeContract` helpers from `test_events_swaps.py`, or redefine locally):

```python
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
```

---

## Discipline

- Write-then-verify each ABI edit.
- Verify the Curve liquidity arity / field sets against the real 3pool ABI — this is the highest-risk item in the phase.
- `record()` stays a stub; do not wire it into `apply()`.
- New subclasses mirror the existing event files' header and structure.

---

## Acceptance

- `balancer/Vault.json` has `PoolBalanceChanged`; `curve/StableSwap.json` has `AddLiquidity` + `RemoveLiquidity` (3-coin); all parse and retain prior entries.
- `EventType.POOL_BALANCE_CHANGED` / `ADD_LIQUIDITY` / `REMOVE_LIQUIDITY` exist; `InitEvent` maps them; the three subclasses exist and are exported.
- `apply(EventType.POOL_BALANCE_CHANGED, address=Vault, argument_filters={'poolId': pid})` returns that pool's joins+exits; `apply(EventType.ADD_LIQUIDITY/REMOVE_LIQUIDITY, address=3pool)` returns those events.
- Phase 3 swap tests still pass; full suite green.

This completes Balancer/Curve event coverage for web3scout: swaps (all protocols) + liquidity (Balancer `PoolBalanceChanged`, 3-coin Curve add/remove). Anything further — Curve removal variants, non-3-coin arities, NG events, factory/creation events, and the curated `record()` output — is deferred and out of scope.

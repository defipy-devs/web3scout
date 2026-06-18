# Web3Scout — Phase 3: Balancer & Curve Swap Events (Claude Code Handoff)

**Status:** Ready for Claude Code
**Spec:** `doc/WEB3SCOUT_EVENTS_BALANCER_CURVE_SPEC.md` (decisions locked)
**Phase:** 3 of 4 (Swaps; Phase 4 is liquidity events)
**Repo:** `web3scout` only
**Prerequisite:** Phases 1/2 (Balancer/Curve read ABIs + enums) merged.

---

## Goal

`RetrieveEvents(connect, abi).apply(EventType.SWAP, address=…)` returns swap events for Balancer and Curve, matching the **current** V2/V3 `apply()` output (the generic `reorg_event_record` shape — `{blockNumber, event, address, …, args}`). No `record()` work — decision #1.

- **Curve:** `apply(EventType.SWAP, address=POOL)` → `TokenExchange` events off the pool.
- **Balancer:** `apply(EventType.SWAP, address=Addr.BALANCER_V2_VAULT, argument_filters={'poolId': pid})` → that pool's `Swap` events off the Vault. Omit `argument_filters` to read all pools.

---

## Tasks

### 1. Add swap events to the ABIs

These are the Phase 1/2 files; add an `events` entry to each `abi` array (keep the existing view functions).

**`python/prod/configs/balancer/Vault.json`** — add the `Swap` event to the `abi` list:

```json
{"anonymous": false, "inputs": [
  {"indexed": true,  "internalType": "bytes32",          "name": "poolId",    "type": "bytes32"},
  {"indexed": true,  "internalType": "contract IERC20",  "name": "tokenIn",   "type": "address"},
  {"indexed": true,  "internalType": "contract IERC20",  "name": "tokenOut",  "type": "address"},
  {"indexed": false, "internalType": "uint256",          "name": "amountIn",  "type": "uint256"},
  {"indexed": false, "internalType": "uint256",          "name": "amountOut", "type": "uint256"}
], "name": "Swap", "type": "event"}
```

**`python/prod/configs/curve/StableSwap.json`** — add the `TokenExchange` event (Vyper-style, no `internalType`):

```json
{"name": "TokenExchange", "anonymous": false, "type": "event", "inputs": [
  {"indexed": true,  "name": "buyer",         "type": "address"},
  {"indexed": false, "name": "sold_id",       "type": "int128"},
  {"indexed": false, "name": "tokens_sold",   "type": "uint256"},
  {"indexed": false, "name": "bought_id",     "type": "int128"},
  {"indexed": false, "name": "tokens_bought", "type": "uint256"}
]}
```

**Verify before trusting** (same discipline as Phase 2's index-type caveat): confirm these signatures against the verified ABIs of the canonical Balancer V2 Vault (`0xBA12222222228d8Ba445958a75a0704d566BF2C8`) and Curve 3pool (`0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7`) on a block explorer — in particular that 3pool's `TokenExchange.buyer` is `address indexed` and `sold_id`/`bought_id` are `int128`. A wrong topic0 means the filter silently matches nothing.

No MANIFEST.in change — same filenames, just more entries.

### 2. Balancer V2 Vault address constant

New file `python/prod/enums/addresses_enum.py`:

```python
# Copyright 2023–2025 Ian Moore
# (Apache-2.0 header — match the other enum files verbatim)

from dataclasses import dataclass

@dataclass(frozen=True)
class AddressesEnum:

    # Balancer V2 Vault — deterministic singleton, same address on every
    # chain Balancer V2 is deployed to (Ethereum, Polygon, Arbitrum, …).
    BALANCER_V2_VAULT: str = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
```

Export it in `python/prod/__init__.py` alongside the other enum aliases:

```python
from .enums.addresses_enum import AddressesEnum as Addr
```

### 3. Extend `SwapEvent.filter()`

`python/prod/event/swap_event.py` — replace only the `filter` method. Leave `record()` and the `_uni_v2_record`/`_uni_v3_record` helpers untouched (decision #1: `record()` stays V2/V3-only and orphaned; Balancer/Curve swaps use the generic path):

```python
    def filter(self, contract, addr = None, fromBlock = None, toBlock = None, argument_filters = None):
        # Curve names its swap event TokenExchange; Uniswap and Balancer both use Swap.
        # Balancer scopes to one pool via argument_filters={'poolId': <bytes32>};
        # Uniswap/Curve pass no argument_filters (events are per-pool already).
        event_names = {e.get('name') for e in contract.abi if e.get('type') == 'event'}
        evt = contract.events.TokenExchange if 'TokenExchange' in event_names else contract.events.Swap
        if argument_filters:
            return evt.create_filter(fromBlock = fromBlock, toBlock = toBlock, argument_filters = argument_filters)
        return evt.create_filter(fromBlock = fromBlock, toBlock = toBlock)
```

Do not add a `record()` branch for Balancer/Curve. If the temptation arises, note it in a followups doc — it belongs to the separate `record()`-reconnection initiative, not here.

### 4. Thread `argument_filters` through `RetrieveEvents`

`python/prod/event/process/retrieve_events.py` — extend `apply` and `gen_read_events`. The conditional pass keeps every other event subclass (Mint/Burn/Sync/Transfer/Create) untouched — they are never called with `argument_filters`:

```python
    def apply(self, event_type, address = None, start_block = None, end_block = None, argument_filters = None):

        assert self.__connect.is_connect(), 'WEB3SCOUT Event Reader: NOT_CONNECTED'
        assert address != None, 'WEB3SCOUT Event Reader: NO_ADDRESS'

        self.__contract = self.retrieve_contract(address)
        event = InitEvent().apply(self.__connect, event_type)
        read_events = self.gen_read_events(event, start_block, end_block, argument_filters)
        return self.to_dict(read_events)
```

```python
    def gen_read_events(self, event, start_block = None, end_block = None, argument_filters = None):
        s_block = 1 if start_block == None else start_block
        e_block = self.latest_block() if end_block == None else end_block
        if argument_filters is not None:
            event_filt = event.filter(self.__contract, fromBlock=s_block, toBlock=e_block, argument_filters=argument_filters)
        else:
            event_filt = event.filter(self.__contract, fromBlock=s_block, toBlock=e_block)
        read_events = event_filt.get_all_entries()
        return read_events
```

### 5. Tests

`tests/test_events_swaps.py` — source-level for ABIs/enums/wiring, plus a real unit test of the filter branch (it needs no live chain — `SwapEvent.__init__` takes `connect` but `filter()` never uses it, so pass `None`):

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
```

(If `import web3scout` is fragile in the env, the `importorskip` cleanly skips the behavior tests; the source-level tests still run.)

---

## Discipline

- Write-then-verify each ABI edit (re-read, confirm it parses and the event is present).
- Touch only `SwapEvent.filter()` and `RetrieveEvents.apply`/`gen_read_events`. Do NOT modify Mint/Burn/Sync/Transfer/Create events — the conditional pass keeps them out of the `argument_filters` path.
- No `record()` changes. No new EventType (SWAP is reused).
- Verify the event signatures against the real contracts before declaring done.

---

## Acceptance

- `balancer/Vault.json` has the `Swap` event; `curve/StableSwap.json` has `TokenExchange`; both still parse and retain their Phase 1/2 view functions.
- `Addr.BALANCER_V2_VAULT` importable from `web3scout`.
- `SwapEvent.filter()` selects `TokenExchange` vs `Swap` from `contract.abi` and forwards `argument_filters` when present.
- `RetrieveEvents.apply(..., argument_filters=…)` threads through; existing V2/V3 call sites unaffected.
- `tests/test_events_swaps.py` passes; full suite green.
- Manual/live: a Balancer pool's swaps read by poolId off the Vault; a Curve 3pool's `TokenExchange` reads off the pool.

Phase 3 is independently shippable: swaps work across all three protocols. Phase 4 adds liquidity events.

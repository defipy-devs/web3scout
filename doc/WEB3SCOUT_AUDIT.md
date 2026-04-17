# Web3Scout — Deep Audit Report

**Date:** April 16, 2026  
**Scope:** Full line-by-line audit of all production source files in `python/prod/`  
**Files audited:** 35 Python source files across abi, contract, data, enums, event, token, uniswap_v2, and utils packages

---

## 1. Critical Finding: eth_defi Dependency Still Exists

Despite the understanding that web3scout is fully self-contained, two files import directly from the `eth_defi` package (web3-ethereum-defi):

**`event/tools/rpc_reorganization_monitor.py`:**
```python
from eth_defi.event_reader.block_header import BlockHeader
```

**`data/reorganization_monitor.py`:**
```python
from eth_defi.event_reader.block_header import BlockHeader, Timestamp
```

This means web3scout requires `eth_defi` installed to use chain reorganization monitoring. Since `RetrieveEvents.latest_block()` instantiates `JSONRPCReorganizationMonitor`, and the agents call `RetrieveEvents`, the entire agent chain transitively depends on `eth_defi`.

**Fix:** Extract `BlockHeader` and `Timestamp` into web3scout as local dataclasses. They're likely simple structs — just `block_number`, `block_hash`, `timestamp` fields. Copy the definition, credit the source, remove the import.

**Severity:** CRITICAL — contradicts the self-contained design intent and adds an untracked dependency.

---

## 2. Bugs (Will Crash at Runtime)

### BUG-1: `convert_hex_bytes_to_string` — wrong variable name in branches

**File:** `event/tools/conversion.py`

```python
def convert_hex_bytes_to_string(self, raw: bytes | HexBytes) -> str:
    if isinstance(raw, HexBytes):
        return raw.hex()
    elif isinstance(data, bytes):   # ← 'data' is UNDEFINED, should be 'raw'
        return raw.hex()
    elif isinstance(data, str):     # ← 'data' is UNDEFINED, should be 'raw'
        return raw
```

Both `elif` branches reference `data` instead of `raw`. If input is plain `bytes` or `str`, this raises `NameError`.

**Severity:** CRITICAL — crashes on non-HexBytes input.

---

### BUG-2: `FetchToken.get_token_name` and `get_token_supply` — `self.token_address` undefined

**File:** `token/fetch/fetch_token.py`

```python
def get_token_name(self, token_address):
    ...
    except Exception as e:
        print(f"Error fetching symbol for {self.token_address}: {e}")  # ← should be token_address
```

```python
def get_token_supply(self, token_address):
    ...
    except Exception as e:
        print(f"Error fetching symbol for {self.token_address}: {e}")  # ← should be token_address
```

Both error handlers reference `self.token_address` but `FetchToken` has no such attribute — `token_address` is the method parameter. Same pattern as the agent layer bugs: error handler crashes, masking the original exception.

Also note: both docstrings say "Fetch the token symbol" — copy-paste from `get_token_symbol`.

**Severity:** CRITICAL — error handling crashes with NameError.

---

### BUG-3: `Token.create_token` calls undefined `deploy_contract`

**File:** `token/token.py`

```python
def create_token(self, web3, deployer, name, symbol, supply, decimals=18):
    return deploy_contract(web3, "ERC20MockDecimals.json", deployer, name, symbol, supply, decimals)
```

`deploy_contract` is a bare function name — not `self.deploy_contract()`, not `Deploy().deploy_contract()`, and not imported from anywhere. This was likely carried over from the original eth_defi source where it was a module-level function.

**Severity:** CRITICAL — crashes on any call.

---

### BUG-4: `Deploy.deploy_contract` references `ABILoading` instead of `ABILoad`

**File:** `contract/deploy.py`

```python
def deploy_contract(self, web3, contract, deployer, *constructor_args, register_for_tracing=True):
    if isinstance(contract, str):
        Contract = ABILoading().get_contract(web3, contract)  # ← ABILoading doesn't exist
```

The class is `ABILoad`, not `ABILoading`. `NameError` on any deployment.

**Severity:** CRITICAL — crashes on contract deployment.

---

### BUG-5: `ABILoad.get_deployed_contract` imports from `pachira`

**File:** `abi/abi_load.py`

```python
def get_deployed_contract(self, web3, fname, address, register_for_tracing=True):
    ...
    if register_for_tracing:
        from pachira.contract.deploy import Deploy  # ← pachira doesn't exist in web3scout
```

This is residual code from the original eth_defi codebase (or a related project called "pachira"). The import will fail unless `pachira` is installed. This method is called by `FetchPairDetails.apply()`, which is called by `SyncEvent._uni_v2_record()`.

**Severity:** HIGH — crashes when `register_for_tracing=True` (the default).

---

### BUG-6: `BaseUtils.find_free_port` calls `is_localhost_port_listening` without `self.`

**File:** `utils/base_utils.py`

```python
def find_free_port(self, ...):
    ...
    if not is_localhost_port_listening(random_port, "127.0.0.1"):  # ← missing self.
```

Same issue in `shutdown_hard`:
```python
if not is_localhost_port_listening(check_port):  # ← missing self.
```

**Severity:** MODERATE — these are utility methods likely unused in production agent workflows, but would crash if called.

---

## 3. Incomplete Implementations

### STUB-1: V3 record methods return empty dicts

**Files:** `event/sync_event.py`, `event/transfer_event.py`

```python
def _uni_v3_record(self, event, abi_load):
    event_record = {}
    return event_record
```

SyncEvent and TransferEvent have no V3 implementation. If an agent points at a V3 pool and receives Sync or Transfer events, it gets back empty dicts — no error, just silent empty data.

**Impact:** Silent data loss for V3 pools. At minimum, raise `NotImplementedError`.

---

### STUB-2: V2 CreateEvent returns empty dict

**File:** `event/create_event.py`

```python
def _uni_v2_record(self, event, abi_load):
    return {}
```

V2 factory PairCreated events produce no data.

---

### STUB-3: SyncEvent and CreateEvent commented out of `__init__.py`

**File:** `event/__init__.py`

```python
#from .sync_event import SyncEvent
#from .create_event import CreateEvent
```

These are still importable via `InitEventEnum` (which imports them directly), but the commented-out lines suggest they may have had import issues at some point.

---

## 4. Architecture Assessment

### What was cherry-picked (from eth_defi)

| Component | Source | Quality |
|-----------|--------|---------|
| `ReadEvents` — chunked eth_getLogs scanner | eth_defi event_reader | Solid, production-grade |
| `ReorganizationMonitor` — chain reorg detection | eth_defi event_reader | Solid, but still imports BlockHeader from eth_defi |
| `Conversion` — raw log data to Python types | eth_defi reader.conversion | Clean utility class |
| `Filter` — topic-based event matching | eth_defi event_reader.filter | Clean dataclass |
| `ABILoad` — contract ABI management with caching | eth_defi abi | Comprehensive, lru_cached |
| `TokenDetails` / `PairDetails` — token/pair data | eth_defi token / uniswap_v2 | Well-structured dataclasses |

### What Ian built on top

| Component | Assessment |
|-----------|-----------|
| `ConnectW3` — simplified Web3 connection | Clean, minimal. The `RPCEnum` fallthrough to use raw URL as provider is a nice touch |
| `FetchToken` — bridge to uniswappy ERC20 | Good idea (unifies web3scout tokens with uniswappy), has error handler bugs |
| `Event` ABC + concrete events | Clean abstract interface. V2 implementations are solid, V3 stubs need completion |
| `RetrieveEvents` — high-level event API | Good abstraction over ReadEvents, clean dict output |
| `InitEventEnum` — event type factory | Nice pattern matching dispatcher |
| `ViewContract` — generic contract view function caller | Unique utility, well-designed |
| Enum system (Platforms, Contracts, Events, Nets, RPCs) | Clean frozen dataclasses |

### Boundary Assessment

The boundary between adapted and original code is well-chosen. The low-level mechanics (log parsing, ABI encoding/decoding, bloom filters, reorg detection) are proven patterns from eth_defi. The high-level abstractions (simplified connection, event type system, token bridging) are Ian's additions that make the library usable without eth_defi's full API surface.

The main issue is that the extraction isn't complete — the `BlockHeader` import and the `pachira` reference are dangling threads from the original codebase that were never cleaned up.

---

## 5. Dependency Analysis

### Declared dependencies (from the code)
- `web3` (Web3.py) — core Ethereum interaction
- `eth_abi` — ABI encoding/decoding
- `eth_typing` — type hints
- `eth_utils` — utility functions
- `eth_bloom` — bloom filter for event matching
- `hexbytes` — hex byte handling
- `pandas` — dataframe conversion in RetrieveEvents
- `psutil` — process management in BaseUtils
- `cachetools` — LRU cache for token details
- `tqdm` — progress bars
- `uniswappy` — ERC20 class (in FetchToken)

### Undeclared dependencies (will crash without)
- `eth_defi` — BlockHeader import in reorg monitoring
- `eth_tester` — TransactionFailed exception in token.py
- `pachira` — circular import in ABILoad.get_deployed_contract

### Dependencies that could be removed
- `psutil` — only used in `BaseUtils.shutdown_hard`, which is a process management utility unlikely to be used in production
- `eth_tester` — only used for exception type in a tuple, could be replaced with a generic catch
- `pandas` — only used in `RetrieveEvents.to_dataframe` and `ReorganizationMonitor` serialization

---

## 6. Relevance to New Agent Layer

### What the new agents need from web3scout

| Capability | Currently Available | Status |
|-----------|-------------------|--------|
| Connect to EVM node | `ConnectW3` | Working |
| Load contract ABIs | `ABILoad` | Working |
| Fetch token metadata | `FetchToken` | Working (has error handler bugs) |
| Read historical events | `RetrieveEvents` | Working |
| Parse Swap events | `SwapEvent` | V2 + V3 working |
| Parse Sync events | `SyncEvent` | V2 working, V3 stub |
| Parse Mint/Burn events | `MintEvent` / `BurnEvent` | V2 + V3 working |
| Detect chain reorgs | `JSONRPCReorganizationMonitor` | Working but requires eth_defi |
| Live event streaming | Not implemented | **Gap** — only batch/historical reads |
| Multi-pool monitoring | Not implemented | **Gap** — single contract per RetrieveEvents |
| Subscription management | Not implemented | **Gap** — no websocket support |

The two biggest gaps for the new agent layer are live event streaming (websocket subscriptions) and multi-pool monitoring. The current `RetrieveEvents` does batch reads over block ranges, which works for backtesting but not for real-time agent operation. Adding websocket support to `ConnectW3` and a streaming variant of `RetrieveEvents` would fill this gap.

---

## 7. Errata Patch — 6 Fixes

### FIX 1 — `conversion.py` → `convert_hex_bytes_to_string`

```python
# Before:
elif isinstance(data, bytes):
    return raw.hex()
elif isinstance(data, str):
    return raw

# After:
elif isinstance(raw, bytes):
    return raw.hex()
elif isinstance(raw, str):
    return raw
```

### FIX 2 — `fetch_token.py` → `get_token_name` error handler

```python
# Before:
print(f"Error fetching symbol for {self.token_address}: {e}")

# After:
print(f"Error fetching name for {token_address}: {e}")
```

### FIX 3 — `fetch_token.py` → `get_token_supply` error handler

```python
# Before:
print(f"Error fetching symbol for {self.token_address}: {e}")

# After:
print(f"Error fetching supply for {token_address}: {e}")
```

### FIX 4 — `deploy.py` → `deploy_contract`

```python
# Before:
Contract = ABILoading().get_contract(web3, contract)

# After:
Contract = ABILoad().get_contract(web3, contract)
```

### FIX 5 — `abi_load.py` → `get_deployed_contract` remove pachira import

```python
# Before:
from pachira.contract.deploy import Deploy

# After:
from ..contract.deploy import Deploy
```

### FIX 6 — Extract `BlockHeader` locally to remove eth_defi dependency

Create `web3scout/python/prod/data/block_header.py`:
```python
from dataclasses import dataclass
from typing import Optional

Timestamp = int

@dataclass(slots=True)
class BlockHeader:
    block_number: int
    block_hash: str
    timestamp: Optional[Timestamp] = None
```

Then update imports in `rpc_reorganization_monitor.py` and `reorganization_monitor.py` to use the local version.

---

## 8. Files Audited (Complete List)

| File | Status |
|------|--------|
| `__init__.py` | Read — clean, explicit imports |
| `abi/abi_load.py` | Read — BUG-5 (pachira import), otherwise comprehensive |
| `contract/deploy.py` | Read — BUG-4 (ABILoading typo) |
| `contract/view.py` | Read — clean, unique utility |
| `contract/__utils__.py` | Read — clean |
| `data/filter.py` | Read — clean |
| `data/pair.py` | Read — clean, well-documented |
| `data/token_details.py` | Read — clean |
| `data/reorganization_monitor.py` | Read — eth_defi dependency |
| `data/chain_reorganization_resolution.py` | Read — clean |
| `enums/contracts_enum.py` | Read — clean |
| `enums/event_type_enum.py` | Read — clean |
| `enums/init_event_enum.py` | Read — clean dispatcher |
| `enums/nets_enum.py` | Read — clean |
| `enums/platforms_enum.py` | Read — clean |
| `enums/rpcs_enum.py` | Read — clean |
| `event/__init__.py` | Read — SyncEvent/CreateEvent commented out |
| `event/event.py` | Read — clean ABC |
| `event/burn_event.py` | Read — V2+V3 working |
| `event/create_event.py` | Read — V2 stub, V3 working |
| `event/mint_event.py` | Read — V2+V3 working |
| `event/swap_event.py` | Read — V2+V3 working |
| `event/sync_event.py` | Read — V2 working, V3 stub |
| `event/transfer_event.py` | Read — V2 working, V3 stub |
| `event/process/read_events.py` | Read — solid, from eth_defi |
| `event/process/retrieve_events.py` | Read — clean high-level API |
| `event/tools/chain_reorganization_detection.py` | Read — clean exception class |
| `event/tools/conversion.py` | Read — BUG-1 |
| `event/tools/log_context.py` | Read — clean |
| `event/tools/log_result.py` | Read — clean TypedDict |
| `event/tools/rpc_reorganization_monitor.py` | Read — eth_defi dependency |
| `token/token.py` | Read — BUG-3 (undefined deploy_contract) |
| `token/fetch/fetch_token.py` | Read — BUG-2 |
| `uniswap_v2/fetch_pair_details.py` | Read — clean |
| `utils/base_utils.py` | Read — BUG-6, some dead utility code |
| `utils/connect.py` | Read — clean, minimal |
| `utils/progress_update.py` | Read — clean Protocol class |

---

## 9. Bottom Line

Web3scout is a well-conceived extraction from web3-ethereum-defi. The cherry-picking was thoughtful — the pieces selected form a coherent toolkit for EVM event reading, and the abstractions built on top are clean and purposeful. The `Event` ABC with protocol-specific dispatch, the `FetchToken` bridge to uniswappy, and the `ViewContract` utility are all good additions.

The main issues are incomplete cleanup from the extraction: the `eth_defi` import for `BlockHeader`, the `pachira` circular import, and the `ABILoading` typo are all artifacts of code that was moved but not fully adapted. The error handler bugs (`self.token_address`, `data` vs `raw`) follow the same copy-paste pattern seen in the agent layer.

For the new agent layer, web3scout provides solid batch event reading infrastructure. The gaps are in live streaming (websocket subscriptions) and multi-pool monitoring, which will need to be added for real-time agent operation.

Six fixes are needed before building on top of this. The most important is extracting `BlockHeader` locally to remove the hidden `eth_defi` dependency — everything else is one-line corrections.

---

## 10. Unit Test Plan

**Instruction to Claude Code:** Build a full test suite for web3scout. Apply the 6 errata fixes from `ERRATA_FIXES.md` FIRST, then build these tests. All tests must pass without a live Web3 connection — mock all RPC calls. Use `pytest` with fixtures.

### Test File Structure

```
tests/
    conftest.py                          # Shared fixtures: mock Web3, mock ABIs, sample events
    test_data/
        test_block_header.py             # BlockHeader dataclass (after FIX 6 extraction)
        test_filter.py                   # Filter dataclass construction + serialization
        test_pair.py                     # PairDetails dataclass
        test_token_details.py            # TokenDetails dataclass
        test_reorganization_monitor.py   # Base ReorganizationMonitor logic (no RPC)
    test_enums/
        test_enums.py                    # All enum classes: members exist, values correct, frozen
    test_abi/
        test_abi_load.py                 # Load JSON ABIs from configs/, get_contract, get_deployed_contract
    test_event/
        test_event_abc.py                # Event ABC interface contract
        test_swap_event.py               # SwapEvent V2 + V3 record parsing
        test_mint_event.py               # MintEvent V2 + V3 record parsing
        test_burn_event.py               # BurnEvent V2 + V3 record parsing
        test_sync_event.py               # SyncEvent V2 record parsing (V3 is stub — test raises NotImplementedError or returns empty)
        test_transfer_event.py           # TransferEvent V2 record parsing
        test_create_event.py             # CreateEvent record parsing
    test_event_tools/
        test_conversion.py               # Conversion utility: hex_to_address, hex_to_int, hex_bytes_to_string (after FIX 1)
        test_log_result.py               # LogResult TypedDict structure
        test_log_context.py              # LogContext TypedDict structure
    test_event_process/
        test_read_events.py              # ReadEvents with mock Web3 provider
        test_retrieve_events.py          # RetrieveEvents with mock Web3 + mock events
    test_token/
        test_fetch_token.py              # FetchToken with mock contract calls (after FIX 2/3)
    test_contract/
        test_view_contract.py            # ViewContract with mock contract
        test_deploy.py                   # Deploy with mock Web3 (after FIX 4)
    test_utils/
        test_connect.py                  # ConnectW3 with mock provider
        test_base_utils.py               # BaseUtils utility methods
    test_uniswap_v2/
        test_fetch_pair_details.py       # FetchPairDetails with mock pair contract
```

### Layer 1 — Pure Data (No Mocking Required)

These tests validate dataclasses, enums, and pure functions with zero external dependencies:

**`test_block_header.py`:**
- Construct `BlockHeader(block_number=100, block_hash="0xabc", timestamp=1700000000)`
- Verify all fields accessible
- Test `timestamp=None` (optional)
- Test `to_pandas()` with list of BlockHeaders
- Test `from_pandas()` roundtrip

**`test_filter.py`:**
- Construct `Filter` with contract address and topics
- Verify `get_bloom_bits()` returns valid bloom filter
- Test topic matching logic

**`test_pair.py`:**
- Construct `PairDetails` with mock token data
- Verify all field access
- Test string representation

**`test_token_details.py`:**
- Construct `TokenDetails` with name, symbol, decimals, supply
- Verify field access
- Test edge cases: 0 decimals, very large supply

**`test_enums.py`:**
- Verify `EventTypeEnum` has all expected event types (Sync, Swap, Mint, Burn, Transfer, Create)
- Verify `NetsEnum` has expected networks
- Verify `PlatformsEnum` has expected platforms (SushiSwap, UniswapV2, UniswapV3)
- Verify `ContractsEnum` has expected contract types
- Verify `RPCEnum` has expected RPC URLs
- Verify all enums are iterable and members are non-None

**`test_conversion.py`:**
- `convert_uint256_bytes_to_address` with known hex bytes → checksummed address
- `convert_int256_bytes_to_int` with known hex bytes → correct integer
- `convert_hex_bytes_to_string` with HexBytes input → hex string
- `convert_hex_bytes_to_string` with raw bytes input → hex string (tests FIX 1)
- `convert_hex_bytes_to_string` with str input → same string (tests FIX 1)
- `decode_data` with sample ABI-encoded event data

**`test_reorganization_monitor.py`:**
- Test base class block tracking: `update_block()`, `check_block_reorg()`
- Test reorg detection with simulated block hash changes
- Test `get_last_block_read()` after sequential updates
- No RPC — subclass `ReorganizationMonitor` with injected block data

### Layer 2 — ABI and Config (Filesystem Only)

**`test_abi_load.py`:**
- `ABILoad().get_abi_fname("erc/ERC20.json")` returns valid path
- `ABILoad().get_abi_fname("sushi/UniswapV2Pair.json")` returns valid path
- `ABILoad().get_abi_fname("uniswap_v3/UniswapV3Pool.json")` returns valid path
- `ABILoad().get_abi_fname("nonexistent.json")` raises appropriate error
- Loaded ABI JSON is valid (has "abi" key with list of function/event defs)
- `get_contract()` with mock Web3 returns a Contract object
- `get_deployed_contract()` with mock Web3 and address returns a Contract object (tests FIX 5 — no pachira import)

### Layer 3 — Event Parsing (Mock Event Data)

Create fixtures with sample raw event log data (matching real Uniswap V2/V3 event structures):

**`conftest.py` fixtures:**
```python
@pytest.fixture
def mock_web3():
    """Mock Web3 instance with minimal provider"""
    ...

@pytest.fixture  
def mock_abi_load():
    """ABILoad instance pointing to real config JSONs"""
    return ABILoad()

@pytest.fixture
def sample_v2_swap_event():
    """Raw event dict matching UniswapV2Pair.Swap event structure"""
    return {
        "topics": [HexBytes("0xd78ad95..."), ...],
        "data": "0x...",
        "address": "0xPoolAddress",
        "blockNumber": 18000000,
        "transactionHash": HexBytes("0xtx..."),
        "logIndex": 0,
    }

@pytest.fixture
def sample_v2_sync_event():
    """Raw event dict matching UniswapV2Pair.Sync event structure"""
    ...

@pytest.fixture
def sample_v2_mint_event():
    """Raw event dict matching UniswapV2Pair.Mint event structure"""
    ...

@pytest.fixture
def sample_v2_burn_event():
    """Raw event dict matching UniswapV2Pair.Burn event structure"""
    ...

@pytest.fixture
def sample_v3_swap_event():
    """Raw event dict matching UniswapV3Pool.Swap event structure"""
    ...
```

**`test_swap_event.py`:**
- Parse V2 swap event → verify amount0In, amount1In, amount0Out, amount1Out extracted
- Parse V3 swap event → verify amount0, amount1, sqrtPriceX96, liquidity, tick extracted
- Verify `get_event_name()` returns "Swap"
- Verify `get_contract_event()` returns correct ABI event reference

**`test_mint_event.py`:**
- Parse V2 mint → verify sender, amount0, amount1
- Parse V3 mint → verify owner, tickLower, tickUpper, amount, amount0, amount1

**`test_burn_event.py`:**
- Parse V2 burn → verify sender, amount0, amount1, to
- Parse V3 burn → verify owner, tickLower, tickUpper, amount, amount0, amount1

**`test_sync_event.py`:**
- Parse V2 sync → verify reserve0, reserve1
- V3 stub → verify returns empty dict (document as known limitation)

**`test_transfer_event.py`:**
- Parse V2 transfer → verify from, to, value
- V3 stub → verify returns empty dict

### Layer 4 — Integration (Mock Web3 Provider)

These tests mock the Web3 provider to test the full event reading pipeline without RPC:

**`test_connect.py`:**
- `ConnectW3("http://localhost:8545")` constructs without error
- `ConnectW3(RPCEnum.value)` constructs with enum RPC
- Verify `w3` property returns a Web3 instance

**`test_fetch_token.py`:**
- Mock contract calls for `name()`, `symbol()`, `decimals()`, `totalSupply()`
- `FetchToken` returns correct `ERC20` object from uniswappy
- Error handlers print correct variable names (tests FIX 2/3 — `token_address` not `self.token_address`)

**`test_view_contract.py`:**
- Mock a contract with a view function
- `ViewContract().apply()` calls the function and returns the result
- Test with different return types (uint256, address, tuple)

**`test_read_events.py`:**
- Mock `web3.eth.get_logs` to return sample events
- `ReadEvents` iterates through blocks and yields events
- Verify chunking behavior (correct block ranges per chunk)
- Verify progress callback is called

**`test_retrieve_events.py`:**
- Mock underlying `ReadEvents` to return sample parsed events
- `RetrieveEvents.apply()` returns list of event dicts
- `RetrieveEvents.to_dataframe()` returns valid DataFrame
- Verify `latest_block()` calls Web3 correctly

**`test_fetch_pair_details.py`:**
- Mock pair contract with `token0()`, `token1()`, `getReserves()`, `factory()`
- `FetchPairDetails().apply()` returns populated PairDetails
- Verify token addresses are checksummed

### Test Data Strategy

Create `tests/fixtures/` with:
- `sample_v2_swap_log.json` — real V2 swap event from mainnet (anonymized)
- `sample_v3_swap_log.json` — real V3 swap event from mainnet (anonymized)
- `sample_v2_sync_log.json` — real V2 sync event
- `sample_v2_mint_log.json` — real V2 mint event
- `sample_v2_burn_log.json` — real V2 burn event

These should be actual JSON from `eth_getLogs` so the parsing tests validate against real data structures.

### Expected Coverage

| Package | Files | Test Files | Coverage Target |
|---------|-------|-----------|----------------|
| `data/` | 6 | 5 | 90%+ |
| `enums/` | 6 | 1 | 100% |
| `abi/` | 1 | 1 | 80%+ |
| `event/` | 7 | 6 | 85%+ (V2 paths) |
| `event/tools/` | 5 | 3 | 90%+ |
| `event/process/` | 2 | 2 | 75%+ (with mocks) |
| `token/` | 2 | 1 | 80%+ |
| `contract/` | 3 | 2 | 75%+ |
| `utils/` | 3 | 2 | 70%+ |
| `uniswap_v2/` | 1 | 1 | 80%+ |
| **Total** | **36** | **24** | **~85%** |

### Prerequisites

1. Apply all 6 errata fixes from `/Users/ian_moore/repos/defipy/ERRATA_FIXES.md` (Fixes 6-11)
2. Verify `grep -r "eth_defi" python/prod/ --include="*.py"` returns zero results
3. Verify `grep -r "pachira" python/prod/ --include="*.py"` returns zero results
4. Then build and run the test suite

### Verification

```bash
cd ~/repos/web3scout
pip install pytest pytest-cov --break-system-packages
python -m pytest tests/ -v --tb=short
python -m pytest tests/ --cov=python/prod --cov-report=term-missing
```

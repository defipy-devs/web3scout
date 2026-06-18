# Web3Scout — Balancer & Curve Stableswap Support

**Status:** Spec (2026-06-18) — ships as **web3scout v1.0.0**
**Predecessor:** `WEB3SCOUT_AUDIT.md`
**Phases:** `PHASE_1_BALANCER_CLAUDE_CODE_HANDOFF.md`, `PHASE_2_CURVE_CLAUDE_CODE_HANDOFF.md`, `WEB3SCOUT_V1_RELEASE_CHECKLIST.md`
**Consumer (deferred):** `defipy/doc/v2_2_execution/DEFIPY_V2_2_LIVEPROVIDER_SPEC.md`
**Purpose:** Define the Balancer (V2 weighted) and Curve (plain Stableswap) ABI + enum additions Web3Scout needs to read those pools. This ships as the web3scout v1 release. DeFiPy v2.2 is the eventual consumer of these reads but is **deferred** — the decision is to ship web3scout v1 standalone first. "v2.2" references below denote that deferred consumer milestone, not the immediate target.

---

## TL;DR

Web3Scout's contribution to the Balancer/Curve work (shipping as **web3scout v1**) is **ABIs and enum registration only** — nothing more. No state-reader classes, no read orchestration, no new event types. DeFiPy's `_rpc.py` orchestrates the actual reads, exactly as it already does for Uniswap V3 (raw selectors over Multicall3, ABI resolved through Web3Scout's `ABILoad`).

This is the "pure" seam decision: Web3Scout stands on its own as the ABI + connection + token-metadata substrate, and DeFiPy pulls it in for Balancer/Curve identically to how it pulls it in for V2/V3.

Concretely, three additions:

1. **Bundled ABIs** under new `configs/balancer/` and `configs/curve/` platform dirs.
2. **`PlatformsEnum`** gains `BALANCER` and `CURVE`.
3. **`JSONContractsEnum`** gains the Balancer Vault / WeightedPool and Curve StableSwap contract names.

After this lands, `ABILoad(Platform.BALANCER, "WeightedPool").apply(w3, addr)` and `ABILoad(Platform.CURVE, "StableSwap").apply(w3, addr)` resolve and return live contract proxies. That is the whole deliverable.

---

## Why this is the entire Web3Scout side

DeFiPy's `LiveProvider` does not call Web3Scout's `FetchPairDetails`, even for V2. The dependency Web3Scout actually carries for the chain-read path is narrow and already proven:

- `ConnectW3` — connection
- `ABILoad` — ABI-by-name resolution (needs the bundled config JSON)
- `FetchToken` — ERC-20 symbol / decimals

V3 reads in DeFiPy go through `_rpc.multicall_aggregate3` against raw function selectors; Web3Scout supplies only the `UniswapV3Pool` ABI (`configs/agnostic/UniswapV3Pool.json`) and the connection. Balancer/Curve follow that precedent exactly. Putting the read orchestration in Web3Scout would diverge from the V3 path and split the read logic across two repos for no benefit. Keep it in one place — DeFiPy — and keep Web3Scout as the ABI substrate.

---

## Scope

### In scope

- `configs/balancer/Vault.json` — Balancer V2 Vault, minimal surface
- `configs/balancer/WeightedPool.json` — Balancer V2 weighted pool, minimal surface
- `configs/curve/StableSwap.json` — Curve plain Stableswap pool, minimal surface
- `PlatformsEnum.BALANCER`, `PlatformsEnum.CURVE`
- `JSONContractsEnum` entries for the three contracts above
- ABILoad resolution tests for each new (platform, contract) pair

### Out of scope

- **State-reader classes** (`FetchBalancerPoolDetails`, etc.). DeFiPy orchestrates. If a standalone reader is ever wanted for Web3Scout's own users, it is a separate, later, demand-driven addition — not part of v2.2.
- **Balancer/Curve event types** (`PoolBalanceChanged`, `TokenExchange`, `AddLiquidity`, `RemoveLiquidity`). The State Twin path needs *state*, not events. Web3Scout's event framework can grow these later if its standalone event users ask. Not load-bearing for v2.2.
- **Balancer V3.** The V3 Vault architecture differs (no per-pool `getPoolId`/`getVault` indirection in the same form, router-centric, buffer/ERC-4626 wrapping). v2.2 targets Balancer **V2** weighted pools, which is what `balancerpy` models.
- **Curve metapools, lending pools, and rate-bearing pools** (stETH/LSD, ERC-4626). These carry non-trivial `stored_rates()` that the plain-pool ABI doesn't surface. v2.2 targets **plain** Stableswap pools (stored_rate = 1, e.g. 3pool).
- **Curve StableSwap-NG dynamic-array reads** beyond what the plain ABI covers. NG's `N_COINS()` / `stored_rates()` are a deferred enhancement; the plain ABI's `coins(i)` / `balances(i)` / `A()` cover the v2.2 target pools.

---

## Additions in detail

### 1. Platform enum

`python/prod/enums/platforms_enum.py`:

```python
@dataclass(frozen=True)
class PlatformsEnum:
    AGNOSTIC: str = "agnostic"
    SUSHI: str = "sushi"
    LOCAL: str = "local"
    UNIV3: str = "uniswap_v3"
    ERC: str = "erc"
    BALANCER: str = "balancer"
    CURVE: str = "curve"
```

The string values must match the `configs/` directory names — `ABILoad` builds the path as `platform + '/' + contract + '.json'`.

### 2. Contract enum

`python/prod/enums/contracts_enum.py` — add:

```python
    BalancerVault: str = "Vault"
    BalancerWeightedPool: str = "WeightedPool"
    CurveStableSwap: str = "StableSwap"
```

Keep the enum value equal to the JSON filename stem (no extension). DeFiPy references these by string through `ABILoad`, so the names are a stable contract — pick them once and don't churn them.

### 3. Bundled ABIs — minimal sufficient surface

ABIs are stored under `configs/<platform>/<Contract>.json`, same `{"abi": [...], "bytecode": ...}` envelope as the existing Uniswap ABIs (bytecode may be empty for address-only reads — `get_contract` only needs `bytecode` when `address is None`). Only the functions DeFiPy reads need to be present; a trimmed ABI keeps the bundle small and the resolution fast.

**`configs/balancer/WeightedPool.json`** — required functions:

- `getPoolId() -> bytes32`
- `getVault() -> address`
- `getNormalizedWeights() -> uint256[]`  (1e18-scaled)
- `getSwapFeePercentage() -> uint256`  (1e18-scaled; carried for future use)
- `totalSupply() -> uint256`  (BPT supply)

**`configs/balancer/Vault.json`** — required functions:

- `getPoolTokens(bytes32 poolId) -> (address[] tokens, uint256[] balances, uint256 lastChangeBlock)`

**`configs/curve/StableSwap.json`** — required functions:

- `A() -> uint256`  (human amplification coefficient — see note below)
- `coins(uint256 i) -> address`
- `balances(uint256 i) -> uint256`
- `fee() -> uint256`  (1e10-scaled; carried for future use)

#### Curve `A()` note

Read `A()`, **not** `A_precise()`. Curve's external `A()` returns the human amplification coefficient (`_A() / A_PRECISION`, `A_PRECISION = 100`); `A_precise()` returns the internal `A * 100`. `stableswappy`'s `A` is the plain coefficient used directly in the invariant, so `A()` is the matching getter. For a pool mid-ramp, `A()` returns the resolved value at the read block, which is exactly what a block-pinned snapshot wants.

#### Balancer `getPoolTokens` is argument-bearing

`getPoolTokens(bytes32)` takes the pool id, so it cannot be read with a no-arg selector. DeFiPy's `_rpc` will encode the calldata — that is a DeFiPy concern (see companion spec). Web3Scout only needs the ABI entry present so the contract proxy exposes the function for DeFiPy's encoder.

---

## Standalone capability after this lands

With the ABIs and enums in place, Web3Scout can resolve and return live Balancer Vault, Balancer WeightedPool, and Curve StableSwap contract proxies through its existing `ABILoad` path — the same standalone capability it offers for `UniswapV3Pool` today. Any Web3Scout user (not just DeFiPy) can load these contracts and call their view functions directly. That is the sense in which Web3Scout "stands on its own": it carries the protocol ABIs and the connection machinery; consumers orchestrate.

Event-framework coverage (Balancer/Curve swap/liquidity events) is a separate, deferred surface and is not required for the DeFiPy State Twin path.

---

## Test plan

Add to `tests/` (Web3Scout's suite covers ABI/import regressions, not live chain):

- **`test_abi_load_balancer`** — `ABILoad(Platform.BALANCER, "Vault")` and `(..., "WeightedPool")` load without error and expose the required function names on the resolved proxy (against a dummy address with a stub w3, or by inspecting the parsed ABI dict).
- **`test_abi_load_curve`** — same for `ABILoad(Platform.CURVE, "StableSwap")`.
- **`test_enum_path_round_trip`** — `ABILoad(Platform.BALANCER, "WeightedPool").get_abi_path()` equals `"balancer/WeightedPool.json"`, etc. Guards against enum-string / directory-name drift.

No live integration tier required here — live reads are exercised in DeFiPy's `test_live_provider_*_live.py` against real pools.

---

## Acceptance

- `configs/balancer/{Vault,WeightedPool}.json` and `configs/curve/StableSwap.json` present, minimal-surface, same envelope as existing ABIs.
- `PlatformsEnum.BALANCER`, `PlatformsEnum.CURVE` added; values match dir names.
- `JSONContractsEnum` entries added; values match filename stems.
- ABILoad resolution tests pass.
- DeFiPy can call `ABILoad(Platform.BALANCER, "WeightedPool").apply(w3, addr)` and `ABILoad(Platform.CURVE, "StableSwap").apply(w3, addr)` and receive working proxies.

Web3Scout is then done for v2.2. The read orchestration that turns these proxies into snapshots lives in DeFiPy.

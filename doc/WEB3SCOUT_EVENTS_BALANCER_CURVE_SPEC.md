# Web3Scout — Balancer & Curve Event Reading (`rEvents.apply`)

**Status:** Spec (2026-06-18) — extends web3scout v1 event coverage
**Predecessor:** `BALANCER_CURVE_SUPPORT_SPEC.md` (added read ABIs + enums, Phases 1/2 done)
**Repo:** `web3scout` only
**Goal:** Make `RetrieveEvents(connect, abi).apply(EventType.X, address=...)` work for Balancer and Curve, the way it already does for Uniswap V2/V3. Phases 1/2 bundled *view-function* ABIs only — no event definitions — so events are a genuinely separate piece.

---

## TL;DR

The event path is: `apply(event_type, address)` → `InitEvent().apply(event_type)` selects an `Event` subclass → `event.filter(contract, fromBlock, toBlock)` builds a web3 filter off the contract's ABI events → `get_all_entries()` → `to_dict()` / `reorg_event_record()` returns one decoded record per event.

To extend it to Balancer/Curve, four things are needed:

1. **Event definitions in the ABIs.** The Phase 1/2 ABIs are view-only. `contract.events.Swap` only resolves if the ABI carries the event. Add events to `balancer/Vault.json` and `curve/StableSwap.json`.
2. **`Event` subclass branches.** `SwapEvent.filter()` hardcodes `contract.events.Swap`; it needs per-protocol branches (Curve's swap is `TokenExchange`, not `Swap`).
3. **A poolId filter path for Balancer.** Balancer events are emitted by the **Vault** (one canonical address) keyed by `poolId` — not by the pool, the way Uniswap emits from the pool. `apply()`/`filter()` need an optional indexed-arg filter to scope to one pool.
4. **`EventType` taxonomy** for the events that don't map onto the Uniswap names.

Two findings below change the shape of this, and there are four decisions I need from you before phasing into Claude Code handoffs.

---

## How the machinery works today

`RetrieveEvents.apply(event_type, address, start_block, end_block)`:

```
contract  = abi.apply(w3, address)            # web3 contract from the passed ABI
event     = InitEvent().apply(event_type)     # EventType -> Event subclass (SwapEvent, ...)
filt      = event.filter(contract, fromBlock, toBlock)   # contract.events.<Name>.create_filter(...)
entries   = filt.get_all_entries()            # web3-DECODED events (AttributeDict, .args/.event)
return to_dict(entries)                        # reorg_event_record() per entry
```

`reorg_event_record(evt)` returns `{blockNumber, event, address, blockHash, logIndex, transactionHash, transactionIndex, args}` — `args` is the full decoded argument dict. The web3 event name is **hardcoded inside each subclass's `filter()`** (`contract.events.Swap`, `contract.events.Sync`, `contract.events.PoolCreated`).

---

## Findings

### F1 — The rich `record()` output is NOT what `apply()` returns (pre-existing, affects V2/V3 too)

The README shows a curated `details` dict (token0/token1/price/amount0In/…). That shape is produced by each subclass's `record()` method, which dispatches per contract (`match contract_type`) and decodes **raw logs** (`event["topics"]`, `decode_data(event["data"])`).

But `apply()` does not call `record()`. It uses `create_filter().get_all_entries()` (web3-decoded AttributeDicts) and formats them with the generic `reorg_event_record()`. `record()` expects the *raw-log* format from the separate `ReadEvents` (`eth_getLogs`) reader, which `apply()` imports but never invokes. So `record()` is effectively orphaned from the `apply()` path, and the current `apply()` output for V2/V3 is the generic `{…, args}` shape, not the README's `details` shape.

This means "make it work like V2/V3" is ambiguous: like the **code's** current V2/V3 `apply()` (generic decoded-args records — small lift), or like the **README's** documented rich output (requires reconnecting `record()`, which is a framework-wide change with V2/V3 regression risk, and is a pre-existing gap unrelated to Balancer/Curve). **This is decision #1.**

My recommendation: scope this spec to **parity with the current code's V2/V3 `apply()`** — the generic decoded-args records. The decoded `args` dict is fully usable (every field, correctly typed). Treat restoring the curated `record()` output as a separate, protocol-agnostic initiative, because it changes V2/V3 behavior and isn't specific to this task.

### F2 — Balancer events live on the Vault, keyed by poolId (not on the pool)

Uniswap (and Curve) emit events from the pool contract, so `apply(event_type, address=pool)` filters that pool's events directly. Balancer V2 emits `Swap` and `PoolBalanceChanged` from the single canonical **Vault** (`0xBA12222222228d8Ba445958a75a0704d566BF2C8`), with `poolId` as an indexed topic.

Consequences:
- For Balancer, the `address` passed to `apply()` is the **Vault**, and the ABI is `balancer/Vault.json` (with events) — a different usage pattern from Uniswap, worth documenting clearly.
- Without a poolId filter, a Balancer read returns *every* pool's events of that type. web3's `create_filter` supports `argument_filters={'poolId': <bytes32>}` on indexed args. So `apply()`/`filter()` need an optional `argument_filters` (or `pool_id`) param threaded through. This is a small, backward-compatible signature extension: `apply(event_type, address, start_block, end_block, argument_filters=None)` → `event.filter(contract, fromBlock, toBlock, argument_filters)`.

### F3 — Event ABIs must be added (Phase 1/2 ABIs are view-only)

`balancer/Vault.json` currently has only `getPoolTokens`. It needs the `Swap` and `PoolBalanceChanged` event definitions. `curve/StableSwap.json` has only `A`/`coins`/`balances`/`fee`; it needs `TokenExchange` (+ liquidity events if in scope). The existing Uniswap ABIs (`agnostic/UniswapV2Pair.json`, `uniswap_v3/UniswapV3Pool.json`) already carry their event entries — mirror that structure.

### F4 — Curve liquidity events are coin-count-specific; the swap event is not

`TokenExchange(address indexed buyer, int128 sold_id, uint256 tokens_sold, int128 bought_id, uint256 tokens_bought)` uses scalar ids/amounts — **coin-count-agnostic**, clean to support for any plain pool.

The liquidity events carry fixed-size arrays baked to `N_COINS`: e.g. 3pool's `AddLiquidity(address indexed provider, uint256[3] token_amounts, uint256[3] fees, uint256 invariant, uint256 token_supply)`. A 2-coin pool's is `uint256[2]`. So a single bundled `StableSwap.json` liquidity-event ABI is **3-coin-specific** and won't decode a 2-coin pool's liquidity events (and the arg arity varies across Curve vintages too). The swap event has no such constraint.

Balancer's `PoolBalanceChanged(bytes32 indexed poolId, address indexed liquidityProvider, IERC20[] tokens, int256[] deltas, uint256[] protocolFeeAmounts)` uses **dynamic** arrays — coin-count-agnostic, clean.

---

## EventType taxonomy (decision #2)

The current enum is Uniswap-centric: `MINT, SWAP, BURN, SYNC, TRANSFER, CREATE`. The protocol events don't all map cleanly:

| Protocol | Swap | Liquidity add | Liquidity remove |
|---|---|---|---|
| Uniswap V2/V3 | `Swap` | `Mint` | `Burn` |
| Balancer V2 (Vault) | `Swap` | `PoolBalanceChanged` (Δ>0) | `PoolBalanceChanged` (Δ<0) |
| Curve (pool) | `TokenExchange` | `AddLiquidity` | `RemoveLiquidity` (+ `…One`, `…Imbalance`) |

Recommended taxonomy:

- **Reuse `EventType.SWAP` across all protocols.** `SwapEvent.filter()`/`record()` gain a per-contract branch (the codebase's existing `match contract_type` idiom): Balancer Vault → `contract.events.Swap`; Curve → `contract.events.TokenExchange`. Users get one consistent "give me swaps" call everywhere — high value.
- **Add protocol-faithful EventTypes for liquidity** rather than mangling into MINT/BURN, because Balancer combines join/exit into one sign-distinguished event and Curve splits removal into three variants: `POOL_BALANCE_CHANGED` (Balancer), `ADD_LIQUIDITY` / `REMOVE_LIQUIDITY` (Curve).

Alternative (decision #2b): introduce a separate `TOKEN_EXCHANGE` type instead of folding Curve swaps under `SWAP`. Cleaner one-event-one-type mapping, but loses the cross-protocol "SWAP" convenience. I lean against it.

---

## Scope

### In scope (recommended)

- **Swaps, all protocols** — the must-have, cleanest piece. `EventType.SWAP` works for Uniswap (unchanged), Balancer (Vault `Swap`, poolId-filterable), Curve (`TokenExchange`).
- **Liquidity events** — Balancer `PoolBalanceChanged`; Curve `AddLiquidity` / `RemoveLiquidity`, **3-coin-scoped** (matching the Phase 2 3pool focus), with the arity caveat documented.
- `argument_filters` plumbing through `apply()`/`filter()` (needed for Balancer poolId).
- Event definitions added to `balancer/Vault.json` and `curve/StableSwap.json`.
- Tests in the source-level harness style, plus gated live tests against the canonical Vault + 3pool.

### Out of scope

- Restoring the curated `record()` output (F1) — separate, V2/V3-affecting initiative unless you fold it in.
- Curve liquidity events for non-3-coin pools, and the `RemoveLiquidityOne` / `RemoveLiquidityImbalance` variants (defer; `AddLiquidity` + `RemoveLiquidity` cover the common case).
- Curve StableSwap-NG event variants.
- Pool/pair creation events for Balancer/Curve (factory `PoolRegistered` / `PlainPoolDeployed`) — a later `CREATE`-style addition.
- Any decoding that requires per-token metadata enrichment beyond the decoded args.

---

## Work by component

1. **ABIs** — add events to `balancer/Vault.json` (`Swap`, `PoolBalanceChanged`) and `curve/StableSwap.json` (`TokenExchange`; `AddLiquidity`/`RemoveLiquidity` 3-coin if in scope). Update MANIFEST.in only if filenames change (they don't — same files, more entries).
2. **`EventTypeEnum`** — add `POOL_BALANCE_CHANGED`, `ADD_LIQUIDITY`, `REMOVE_LIQUIDITY` (per decision #2).
3. **`InitEventEnum`** — map the new types to their `Event` subclasses.
4. **`Event` subclasses** — extend `SwapEvent` with Balancer/Curve branches in `filter()` (event-name selection by `contract_type`) and, if F1 rich output is chosen, `record()`. Add `PoolBalanceChangedEvent`, `AddLiquidityEvent`, `RemoveLiquidityEvent`.
5. **`filter()` signature** — thread `argument_filters` (default `None`) so Balancer can scope by `poolId`. Backward compatible for V2/V3.
6. **`RetrieveEvents.apply()`** — accept and pass `argument_filters` (or `pool_id`). No change to existing call sites.
7. **Tests** — source-level (ABI carries the events; enum/init mapping; filter builds for the new contract types) + gated live (Vault `Swap` for a known pool by poolId; 3pool `TokenExchange`).

---

## Suggested phases (for Claude Code, after decisions locked)

- **Phase 3 — Swaps across Balancer + Curve.** ABIs gain the swap events; `SwapEvent` per-contract branches; `argument_filters` plumbing for the Vault poolId; tests. Highest value, cleanest, no coin-count issues. Independently shippable.
- **Phase 4 — Liquidity events.** New EventTypes + subclasses; Balancer `PoolBalanceChanged`; Curve `AddLiquidity`/`RemoveLiquidity` (3-coin); the arity caveat; tests.

---

## Decisions (locked 2026-06-18)

1. **Output format:** match the current code's V2/V3 `apply()` — generic decoded-args records via `reorg_event_record`. `record()` stays orphaned/untouched; the README/`record()` discrepancy is a separate, protocol-agnostic initiative, not part of this work.
2. **Taxonomy:** reuse `EventType.SWAP` across all protocols (Curve → `TokenExchange` via a `contract.abi` branch in `SwapEvent.filter()`); add `POOL_BALANCE_CHANGED` (Balancer), `ADD_LIQUIDITY` / `REMOVE_LIQUIDITY` (Curve) for liquidity.
3. **Liquidity scope:** swaps (all protocols) + 3-coin Curve liquidity + Balancer `PoolBalanceChanged`. `RemoveLiquidityOne` / `RemoveLiquidityImbalance` and non-3-coin arities deferred.
4. **Balancer usage:** pass the Vault address + optional `poolId` argument filter (Option A) — the honest pairing, since events live on the Vault. The canonical Balancer V2 Vault address is exposed as a constant (`Addr.BALANCER_V2_VAULT`, same `0xBA12…` across chains) so callers don't hardcode it. A pool-address convenience wrapper is deferred (demand-driven).

Handoffs: `PHASE_3_EVENTS_SWAPS_CLAUDE_CODE_HANDOFF.md`, `PHASE_4_EVENTS_LIQUIDITY_CLAUDE_CODE_HANDOFF.md`.

---

## Acceptance (assuming recommended scope)

- `RetrieveEvents(connect, ABILoad(Platform.BALANCER, "Vault")).apply(EventType.SWAP, address=VAULT, argument_filters={'poolId': pid}, start_block=…, end_block=…)` returns that pool's swaps.
- `RetrieveEvents(connect, ABILoad(Platform.CURVE, "StableSwap")).apply(EventType.SWAP, address=pool, …)` returns `TokenExchange` events.
- Liquidity events readable for Balancer (`POOL_BALANCE_CHANGED`) and 3-coin Curve (`ADD_LIQUIDITY`/`REMOVE_LIQUIDITY`).
- V2/V3 `apply()` output unchanged (regression-locked).
- Source-level + gated live tests pass.

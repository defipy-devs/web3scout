# Changelog

All notable changes to Web3Scout are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-06-18

First stable release. Web3Scout now stands on its own as a self-contained
onchain-data substrate with a stable public surface (`ABILoad`, `ConnectW3`,
`FetchToken`, `RetrieveEvents`, and the bundled ABIs) that DeFiPy — and anyone
else — can pin against.

### Added
- **Balancer ABIs** — Balancer V2 `Vault` (`getPoolTokens`) and `WeightedPool`
  (`getPoolId`, `getVault`, `getNormalizedWeights`, `getSwapFeePercentage`,
  `totalSupply`), resolvable via `ABILoad(Platform.BALANCER, ...)`.
- **Curve ABI** — plain `StableSwap` (`A`, `coins`, `balances`, `fee`),
  resolvable via `ABILoad(Platform.CURVE, ...)`. Uses the human amplification
  getter `A()` and `uint256` coin/balance indices (correct for Curve 3pool,
  registry/factory-era, and StableSwap-NG pools).
- `PlatformsEnum.BALANCER` / `PlatformsEnum.CURVE` and the
  `JSONContractsEnum.BalancerVault` / `BalancerWeightedPool` / `CurveStableSwap`
  entries — a stable string contract DeFiPy references.
- Source-level test suites for the Balancer and Curve ABI/enum/packaging
  surface (`tests/test_balancer_abi.py`, `tests/test_curve_abi.py`).

### Changed
- Established Uniswap V2/V3 event retrieval (Swap/Mint/Sync/Burn/Transfer/Create)
  and Uniswap V2 state reads as the stable v1 event/read surface.

### Removed
- **`eth_defi` dependency** — the reorg/block-header modules now import the
  local `data.block_header`; `setup.py` no longer carries `eth_defi`. The
  package is fully self-contained.

### Fixed
- **BUG-1** `convert_hex_bytes_to_string` variable-name crash — uses `raw` in
  all branches with a clean `else: raise TypeError`.
- **BUG-2** `FetchToken` `self.token_address` undefined reference.
- `abi_load` import-path corrections and related regression coverage
  (`test_abi_load.py`, `test_conversion.py`, `test_reorg_monitor.py`,
  `test_block_header.py`, `test_fetch_token.py`).

### Known limitations
- **web3 6.x ceiling.** `web3` is pinned `>= 6.0, < 7.0` because
  `abi_load.py` uses `web3._utils.contracts.get_function_info`, which was
  removed in web3 7.x. The web3 7.x migration is deferred to a later release;
  `import web3scout` requires the web3 6.x stack.

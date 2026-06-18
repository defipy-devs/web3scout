# Web3Scout: Onchain Event Framework for DeFiPy

🔗 SPDX-Anchor: [anchorregistry.ai/AR-2026-5RJKqw5](https://anchorregistry.ai/AR-2026-5RJKqw5)

Web3Scout pulls onchain DeFi data from EVM chains — event retrieval, pool state
reads, and reorg-aware block monitoring — behind a small, stable API (`ABILoad`,
`ConnectW3`, `RetrieveEvents`, `FetchToken`). As of v1 it stands on its own (no
`eth_defi` dependency) and is the substrate DeFiPy — and anyone else — builds on.

## What it does

- **Events** — retrieve Swap, Mint, Sync, Burn, Transfer, and Create events from
  Uniswap V2 / V3 (and forks such as Sushi) via `RetrieveEvents` / `ReadEvents`.
- **State reads** — Uniswap V2 pair reserves and metadata (`FetchPairDetails`),
  plus bundled read ABIs for Balancer (V2 `Vault` / `WeightedPool`) and Curve
  (`StableSwap`) pool state.
- **Multi-protocol ABIs** — Uniswap V2/V3, Sushi, Balancer, Curve, and ERC-20
  ABIs resolvable through one `ABILoad(Platform.X, JSONContract.Y)` interface.
- **Reorg-aware monitoring** — detect and resolve chain reorganizations with
  `ReorganizationMonitor` / `JSONRPCReorganizationMonitor`.
- **Token metadata** — fetch ERC-20 details (symbol, decimals, …) with
  `FetchToken`.

## Installation 
```
> git clone https://github.com/defipy-devs/web3scout
> pip install .
```
or
```
> pip install Web3Scout
```

## Uni V2 Swap Events (Polygon) Example

```
from web3scout import *

abi = ABILoad(Platform.SUSHI, JSONContract.UniswapV2Pair)
connect = ConnectW3(Net.POLYGON)
connect.apply()

rEvents = RetrieveEvents(connect, abi)
last_block = rEvents.latest_block()
start_block = last_block - 3
dict_events = rEvents.apply(EventType.SWAP, start_block=start_block, end_block=last_block)
```

```javascript
swap at block:61,234,918 tx:0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8
swap at block:61,234,918 tx:0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8
swap at block:61,234,918 tx:0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8
swap at block:61,234,918 tx:0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8
.
```

```
dict_events
```

```javascript
{0: {'chain': 'polygon',
  'contract': 'uniswapv2pair',
  'type': 'swap',
  'platform': 'sushi',
  'address': '0x604229c960e5cacf2aaeac8be68ac07ba9df81c3',
  'tx_hash': '0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8',
  'blk_num': 61234918,
  'timestamp': 1725051030,
  'details': {'web3_type': web3._utils.datatypes.Swap,
   'token0': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'token1': '0xbF6f53423F25Df43a057F42A840158D6fDdB45BF',
   'amount0In': 19000000000000000000,
   'amount1Out': 7889648}},
 1: {'chain': 'polygon',
  'contract': 'uniswapv2pair',
  'type': 'swap',
  'platform': 'sushi',
  'address': '0x604229c960e5cacf2aaeac8be68ac07ba9df81c3',
  'tx_hash': '0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8',
  'blk_num': 61234918,
  'timestamp': 1725051030,
  'details': {'web3_type': web3._utils.datatypes.Swap,
   'token0': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'token1': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'amount0In': 0,
   'amount1Out': 0}},
 2: {'chain': 'polygon',
  'contract': 'uniswapv2pair',
  'type': 'swap',
  'platform': 'sushi',
  'address': '0x3c986748414a812e455dcd5418246b8fded5c369',
  'tx_hash': '0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8',
  'blk_num': 61234918,
  'timestamp': 1725051030,
  'details': {'web3_type': web3._utils.datatypes.Swap,
   'token0': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'token1': '0xbF6f53423F25Df43a057F42A840158D6fDdB45BF',
   'amount0In': 21176176598530377323,
   'amount1Out': 796785880798504079}},
 3: {'chain': 'polygon',
  'contract': 'uniswapv2pair',
  'type': 'swap',
  'platform': 'sushi',
  'address': '0x3c986748414a812e455dcd5418246b8fded5c369',
  'tx_hash': '0x9f16c76b6a83ac424ea736fb7dd2b1fc735888f222ee04dc1b1f7b933469faf8',
  'blk_num': 61234918,
  'timestamp': 1725051030,
  'details': {'web3_type': web3._utils.datatypes.Swap,
   'token0': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'token1': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
   'amount0In': 0,
   'amount1Out': 0}}}
```

## Uni V3 Swap Events (Polygon) Example

```
from web3scout import *

abi = ABILoad(Platform.UNIV3, JSONContract.UniswapV3Pool)
connect = ConnectW3(Net.POLYGON)
connect.apply()

rEvents = RetrieveEvents(connect, abi)
last_block = rEvents.latest_block()
start_block = last_block - 15
dict_events = rEvents.apply(EventType.MINT, start_block=start_block, end_block=last_block)
```

```javascript
mint at block:61,391,083 tx:0xe499971b5410e766d00bf4467c6b333cda04577f1068bb676debe72331254365
mint at block:61,391,092 tx:0x29d53602b1bbd67734c2e3deba8ad0a55aa84204a6244e720f24ee5160505213
.
```

```
dict_events
```

```javascript
{0: {'chain': 'polygon',
  'contract': 'uniswapv3pool',
  'type': 'mint',
  'platform': 'uniswap_v3',
  'pool_address': '0xb6e57ed85c4c9dbfef2a68711e9d6f36c56e0fcb',
  'tx_hash': '0xe499971b5410e766d00bf4467c6b333cda04577f1068bb676debe72331254365',
  'blk_num': 61391083,
  'timestamp': 1725401207,
  'details': {'web3_type': web3._utils.datatypes.Mint,
   'owner': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
   'tick_lower': -286090,
   'tick_upper': -284860,
   'liquidity_amount': 884887839988325,
   'amount0': 39958320744269616249,
   'amount1': 17912626}},
 1: {'chain': 'polygon',
  'contract': 'uniswapv3pool',
  'type': 'mint',
  'platform': 'uniswap_v3',
  'pool_address': '0x960fdfe0de1079459493a7e3aa857f8ce0b34016',
  'tx_hash': '0x29d53602b1bbd67734c2e3deba8ad0a55aa84204a6244e720f24ee5160505213',
  'blk_num': 61391092,
  'timestamp': 1725401227,
  'details': {'web3_type': web3._utils.datatypes.Mint,
   'owner': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
   'tick_lower': 22600,
   'tick_upper': 40000,
   'liquidity_amount': 7675592444129481120,
   'amount0': 64052149877205455,
   'amount1': 29656680135133456015}}}
```


## Protocol Coverage

Beyond the Uniswap V2/V3 event examples above, Web3Scout bundles minimal, address-based read ABIs for additional protocols, resolvable through the same `ABILoad` interface:

- **Balancer** — V2 `Vault` and `WeightedPool`:
  `ABILoad(Platform.BALANCER, JSONContract.BalancerVault)` and
  `ABILoad(Platform.BALANCER, JSONContract.BalancerWeightedPool)`
- **Curve** — plain `StableSwap`:
  `ABILoad(Platform.CURVE, JSONContract.CurveStableSwap)`

These cover onchain state reads (pool tokens, balances, normalized weights, swap fee, amplification coefficient).

## Balancer Pool State (Ethereum) Example

The Balancer ABIs are read ABIs for onchain state. `ViewContract` reads every
zero-input getter on a pool in a single call; parameterized calls (such as the
Vault's `getPoolTokens`) use the contract proxy from `ABILoad(...).apply(w3, address)`.

```
from web3scout import *

connect = ConnectW3("https://eth.llamarpc.com")   # any Ethereum mainnet RPC
connect.apply()
w3 = connect.get_w3()

# Balancer V2 80/20 BAL-WETH WeightedPool
pool_addr = "0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56"
pool_abi  = ABILoad(Platform.BALANCER, JSONContract.BalancerWeightedPool)

# Read all zero-input getters at once (verbose=True prints each)
pool_state = ViewContract(connect, pool_abi, verbose=True).apply(pool_addr)
```

```javascript
[0] getPoolId()             b'\x5c\x6e\xe3\x04...'                     # 32-byte pool id
[1] getVault()              0xBA12222222228d8Ba445958a75a0704d566BF2C8
[2] getNormalizedWeights()  [800000000000000000, 200000000000000000]  # 80% / 20% (1e18)
[3] getSwapFeePercentage()  1000000000000000                          # 0.1% (1e18)
[4] totalSupply()           24875403726528338391741
```

Pool token addresses and balances live on the Vault, keyed by the pool id:

```
vault = ABILoad(Platform.BALANCER, JSONContract.BalancerVault).apply(
    w3, "0xBA12222222228d8Ba445958a75a0704d566BF2C8")   # canonical Balancer V2 Vault

tokens, balances, last_change_block = vault.functions.getPoolTokens(
    pool_state["getPoolId"]).call()
```

## Curve Pool State (Ethereum) Example

`ViewContract` reads the zero-input getters (`A`, `fee`); the per-coin getters
take an index, so those go through the contract proxy.

```
from web3scout import *

connect = ConnectW3("https://eth.llamarpc.com")   # any Ethereum mainnet RPC
connect.apply()
w3 = connect.get_w3()

# Curve 3pool (DAI / USDC / USDT)
pool_addr = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
abi = ABILoad(Platform.CURVE, JSONContract.CurveStableSwap)

# Zero-input getters: A (amplification) and fee
state = ViewContract(connect, abi, verbose=True).apply(pool_addr)

# coins(i) / balances(i) take a coin index -> use the proxy
pool = abi.apply(w3, pool_addr)
for i in range(3):
    print(pool.functions.coins(i).call(), pool.functions.balances(i).call())
```

```javascript
[0] A()    2000
[1] fee()  1000000              # 1e10-scaled

0x6B175474E89094C44Da98b954EedeAC495271d0F 412300000000000000000000000   # DAI
0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 398700000000                  # USDC
0xdAC17F958D2ee523a2206206994597C13D831ec7 376500000000                  # USDT
```

> Output values above are illustrative; the addresses (Balancer V2 Vault, Curve
> 3pool, DAI/USDC/USDT) are the canonical Ethereum mainnet contracts.

## Sushi Uniswap V2: Polygon 

* Events (ie, Swap, Mint, Sync, Burn, Transfer): see [notebook](https://github.com/defipy-devs/web3scout/blob/main/notebook/univ2/test_univ2_events.ipynb)

## Uniswap V3: Polygon

* Events (ie, Swap, Mint, Burn, Create): see [notebook](https://github.com/defipy-devs/web3scout/blob/main/notebook/univ3/test_univ3_events.ipynb)



## Testing

Run the full test suite from the repo root:

```
> python -m pytest tests/ -v
```

Tests cover bug fixes and regression checks across:

- **conversion** — hex/bytes string conversion
- **fetch_token** — error handling in token metadata fetches
- **deploy** — contract deployment class references
- **abi_load** — import path corrections
- **reorg_monitor** — chain reorganization monitoring imports
- **block_header** — BlockHeader dataclass (extracted from eth_defi)
- **token** — ERC-20 token creation
- **base_utils** — port scanning utilities

### Requirements

```
> pip install pytest
```

## License
Web3Scout is licensed under the Apache License, Version 2.0.  
See [LICENSE](./LICENSE) and [NOTICE](./NOTICE) for details.  
Portions of this project may include code from third-party projects under compatible open-source licenses.


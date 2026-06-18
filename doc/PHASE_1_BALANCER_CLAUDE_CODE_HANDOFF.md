# Web3Scout v1.0.0 — Phase 1: Balancer Support (Claude Code Handoff)

**Status:** Ready for Claude Code
**Spec:** `doc/BALANCER_CURVE_SUPPORT_SPEC.md`
**Release track:** Phase 1 → Phase 2 → `WEB3SCOUT_V1_RELEASE_CHECKLIST.md` (tag + publish v1.0.0)
**Phase:** 1 of 2 (Balancer; Phase 2 is Curve + sets the 1.0.0 version)
**Repo:** `web3scout` only

---

## Goal

After this phase, `ABILoad(Platform.BALANCER, "WeightedPool").apply(w3, addr)` and `ABILoad(Platform.BALANCER, "Vault").apply(w3, addr)` resolve to working contract proxies, and the ABIs ship in the wheel. Balancer is then fully resolvable. This work ships as part of **web3scout v1**; it is also the substrate DeFiPy v2.2 (deferred) will eventually consume — but v2.2 is not the immediate target, the v1 release is.

Pure ABI + enum + packaging work. No reader classes, no event types, no read orchestration.

---

## Tasks

### 1. Platform enum

`python/prod/enums/platforms_enum.py` — add `BALANCER` to the frozen dataclass:

```python
    BALANCER: str = "balancer"
```

The string value MUST equal the configs subdirectory name — `ABILoad` builds the path as `platform + '/' + contract + '.json'`.

### 2. Contract enum

`python/prod/enums/contracts_enum.py` — add:

```python
    BalancerVault: str = "Vault"
    BalancerWeightedPool: str = "WeightedPool"
```

Enum value = JSON filename stem (no extension). These names are a stable contract DeFiPy references by string — do not churn them later.

### 3. ABI files

Create `python/prod/configs/balancer/` and write two files verbatim.

**`python/prod/configs/balancer/WeightedPool.json`:**

```json
{
  "abi": [
    {"inputs": [], "name": "getPoolId", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getVault", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getNormalizedWeights", "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getSwapFeePercentage", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
  ],
  "bytecode": ""
}
```

**`python/prod/configs/balancer/Vault.json`:**

```json
{
  "abi": [
    {"inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}], "name": "getPoolTokens", "outputs": [{"internalType": "contract IERC20[]", "name": "tokens", "type": "address[]"}, {"internalType": "uint256[]", "name": "balances", "type": "uint256[]"}, {"internalType": "uint256", "name": "lastChangeBlock", "type": "uint256"}], "stateMutability": "view", "type": "function"}
  ],
  "bytecode": ""
}
```

`bytecode` is empty intentionally — `ABILoad.get_contract` only reads `bytecode` when `address is None`. These ABIs are for address-based reads, so empty is correct and keeps the files minimal.

### 4. Packaging — MANIFEST.in

`MANIFEST.in` uses explicit per-file `include` lines, NOT a glob. New files are invisible to the wheel unless listed. Add:

```
include python/prod/configs/balancer/Vault.json
include python/prod/configs/balancer/WeightedPool.json
```

No change needed to `setup.py` `packages=[...]` — configs subdirs are package data, not Python packages, and `include_package_data=True` + MANIFEST.in covers them. The version is set to `1.0.0` in Phase 2; the actual build/tag/publish runs from `WEB3SCOUT_V1_RELEASE_CHECKLIST.md`.

### 5. Tests

`tests/test_balancer_abi.py` — match the existing source-level harness (`tests/conftest.py` provides `read_source`; `import web3scout` is avoided). Use direct file reads and `json.load`:

```python
import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _fn_names(abi_doc):
    return {e["name"] for e in abi_doc["abi"] if e.get("type") == "function"}


class TestBalancerABIs:

    def test_weighted_pool_functions_present(self):
        names = _fn_names(_load_abi("balancer/WeightedPool.json"))
        assert {"getPoolId", "getVault", "getNormalizedWeights",
                "getSwapFeePercentage", "totalSupply"} <= names

    def test_vault_functions_present(self):
        names = _fn_names(_load_abi("balancer/Vault.json"))
        assert "getPoolTokens" in names

    def test_get_pool_tokens_takes_pool_id(self):
        abi = _load_abi("balancer/Vault.json")["abi"]
        fn = next(e for e in abi if e.get("name") == "getPoolTokens")
        assert [i["type"] for i in fn["inputs"]] == ["bytes32"]


class TestBalancerEnums:

    def test_platform_enum_has_balancer(self):
        src = read_source("enums/platforms_enum.py")
        assert 'BALANCER: str = "balancer"' in src

    def test_contract_enum_has_balancer(self):
        src = read_source("enums/contracts_enum.py")
        assert 'BalancerVault: str = "Vault"' in src
        assert 'BalancerWeightedPool: str = "WeightedPool"' in src


class TestBalancerPackaging:

    def test_manifest_includes_balancer_abis(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        assert "python/prod/configs/balancer/Vault.json" in text
        assert "python/prod/configs/balancer/WeightedPool.json" in text
```

If `ABILoad` can be imported in the environment (the eth_utils shim is in place), optionally add a resolution check:

```python
    def test_abi_path_round_trip(self):
        from web3scout.abi.abi_load import ABILoad
        from web3scout.enums.platforms_enum import PlatformsEnum
        a = ABILoad(PlatformsEnum.BALANCER, "WeightedPool")
        assert a.get_abi_path() == "balancer/WeightedPool.json"
```

Guard it with `pytest.importorskip` or a try/except if `import web3scout` is still fragile in this env.

---

## Discipline

- Write-then-verify: after writing each JSON, read it back and confirm it parses.
- Do not add functions beyond the listed surface. Minimal ABI is the spec.
- Do not touch `setup.py` version this phase.
- Do not add event types or reader classes.

---

## Acceptance

- `configs/balancer/Vault.json` + `WeightedPool.json` present, parse, carry exactly the listed functions.
- `PlatformsEnum.BALANCER` and the two `JSONContractsEnum` entries present.
- Both JSONs listed in MANIFEST.in.
- `tests/test_balancer_abi.py` passes; full existing suite still green.
- (If runnable) `ABILoad(Platform.BALANCER, "WeightedPool").get_abi_path() == "balancer/WeightedPool.json"`.

Phase 1 is independently shippable: Balancer is fully resolvable. Phase 2 adds Curve and sets the `1.0.0` version; the v1 release proper runs from `WEB3SCOUT_V1_RELEASE_CHECKLIST.md`.

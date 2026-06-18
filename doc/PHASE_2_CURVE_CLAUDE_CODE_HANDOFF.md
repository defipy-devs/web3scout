# Web3Scout v1.0.0 — Phase 2: Curve Support + Version Set (Claude Code Handoff)

**Status:** Ready for Claude Code (after Phase 1)
**Spec:** `doc/BALANCER_CURVE_SUPPORT_SPEC.md`
**Release track:** Phase 1 → Phase 2 → `WEB3SCOUT_V1_RELEASE_CHECKLIST.md` (tag + publish v1.0.0)
**Phase:** 2 of 2 (Curve; also sets `version='1.0.0'` and completes packaging)
**Repo:** `web3scout` only
**Prerequisite:** Phase 1 (Balancer) merged.

---

## Goal

After this phase, `ABILoad(Platform.CURVE, "StableSwap").apply(w3, addr)` resolves, the Curve ABI ships in the wheel, and the repo is at `version='1.0.0'` with both protocols' ABIs in place. The code work for **web3scout v1** is then complete; the build/tag/publish runs from `WEB3SCOUT_V1_RELEASE_CHECKLIST.md`.

---

## Tasks

### 1. Platform enum

`python/prod/enums/platforms_enum.py` — add:

```python
    CURVE: str = "curve"
```

### 2. Contract enum

`python/prod/enums/contracts_enum.py` — add:

```python
    CurveStableSwap: str = "StableSwap"
```

### 3. ABI file

Create `python/prod/configs/curve/` and write:

**`python/prod/configs/curve/StableSwap.json`:**

```json
{
  "abi": [
    {"name": "A", "inputs": [], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "coins", "inputs": [{"name": "i", "type": "uint256"}], "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"name": "balances", "inputs": [{"name": "i", "type": "uint256"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "fee", "inputs": [], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
  ],
  "bytecode": ""
}
```

**Index type caveat — verify before finalizing.** This ABI uses `uint256` for the `coins` / `balances` index, which is correct for the v2.2 target (Curve 3pool, `0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7`, and all registry/factory-era and StableSwap-NG pools). The *legacy* lending pools (Compound, Y, BUSD, PAX — deployed 2020) use `int128` for these indices. If the read path is ever pointed at one of those, the selector won't match and reads revert. For v2.2 (plain modern pools) `uint256` is right; confirm against the verified ABI of the specific target pool on a block explorer before trusting it. Do not add an `int128` variant in this phase — out of scope.

`A` is the human amplification getter (`A_precise()` returns `A * A_PRECISION`, A_PRECISION = 100); `stableswappy`'s `A` is the plain coefficient, so `A()` is the correct getter. Do not include `A_precise`.

### 4. Packaging — MANIFEST.in + version bump

`MANIFEST.in` — add:

```
include python/prod/configs/curve/StableSwap.json
```

`setup.py` — set the version. This is the final code phase, so the repo lands at the release version here; the actual build/tag/publish is the separate v1 release step (`WEB3SCOUT_V1_RELEASE_CHECKLIST.md`):

```python
      version='1.0.0',
```

(0.2.0 → 1.0.0: first stable release. Balancer + Curve complete the multi-protocol ABI surface, and the package is self-contained — the eth_defi dependency was removed and the v1.x line commits to a stable `ABILoad` / `ConnectW3` / `FetchToken` surface for DeFiPy to pin against.)

### 5. Tests

`tests/test_curve_abi.py` — same source-level pattern as Phase 1:

```python
import json
import os
import pytest
from conftest import read_source, PROD_PATH


def _load_abi(relpath):
    with open(os.path.join(PROD_PATH, "configs", relpath)) as f:
        return json.load(f)


def _fn(abi_doc, name):
    return next(e for e in abi_doc["abi"]
               if e.get("type") == "function" and e.get("name") == name)


class TestCurveABI:

    def test_functions_present(self):
        abi = _load_abi("curve/StableSwap.json")
        names = {e["name"] for e in abi["abi"] if e.get("type") == "function"}
        assert {"A", "coins", "balances", "fee"} <= names

    def test_coins_index_is_uint256(self):
        abi = _load_abi("curve/StableSwap.json")
        assert [i["type"] for i in _fn(abi, "coins")["inputs"]] == ["uint256"]
        assert [i["type"] for i in _fn(abi, "balances")["inputs"]] == ["uint256"]

    def test_uses_human_A_not_precise(self):
        abi = _load_abi("curve/StableSwap.json")
        names = {e["name"] for e in abi["abi"] if e.get("type") == "function"}
        assert "A" in names
        assert "A_precise" not in names


class TestCurveEnums:

    def test_platform_enum_has_curve(self):
        src = read_source("enums/platforms_enum.py")
        assert 'CURVE: str = "curve"' in src

    def test_contract_enum_has_curve(self):
        src = read_source("enums/contracts_enum.py")
        assert 'CurveStableSwap: str = "StableSwap"' in src


class TestPackagingCloseout:

    def test_manifest_includes_curve_abi(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        assert "python/prod/configs/curve/StableSwap.json" in text

    def test_version_bumped(self):
        setup_py = os.path.join(PROD_PATH, "..", "..", "setup.py")
        with open(setup_py) as f:
            text = f.read()
        assert "version='1.0.0'" in text

    def test_both_protocols_packaged(self):
        manifest = os.path.join(PROD_PATH, "..", "..", "MANIFEST.in")
        with open(manifest) as f:
            text = f.read()
        for rel in ("balancer/Vault.json", "balancer/WeightedPool.json",
                    "curve/StableSwap.json"):
            assert "python/prod/configs/" + rel in text
```

---

## Discipline

- Write-then-verify each file.
- Minimal ABI surface only.
- Verify the `uint256` index assumption against the target pool's real ABI (caveat above) before declaring done.

---

## Acceptance

- `configs/curve/StableSwap.json` present, parses, carries `A` / `coins` / `balances` / `fee` with `uint256` indices and no `A_precise`.
- `PlatformsEnum.CURVE` and `JSONContractsEnum.CurveStableSwap` present.
- Curve ABI in MANIFEST.in; `setup.py` version = `0.3.0`.
- `tests/test_curve_abi.py` passes; Phase 1 Balancer tests still pass; full suite green.
- Both protocols' ABIs are packaged (the `test_both_protocols_packaged` check).

---

## Milestone close

After Phase 2 the repo is at `version='1.0.0'` with Balancer + Curve fully resolvable and packaged. The code work is done. The actual release — build, wheel-contents verification, clean-venv smoke install, tag, PyPI publish, README/CHANGELOG — is the **v1 release**, tracked separately in `WEB3SCOUT_V1_RELEASE_CHECKLIST.md`. Do that next.

DeFiPy v2.2 is **deferred** (decision: hold v2.2, ship web3scout v1 first). When v2.2 resumes, its packaging step is bumping the `chain` / `book` / `agentic` extras in `defipy/setup.py` from `web3scout >= 0.2.0` to `>= 1.0.0`. No DeFiPy change is needed for the web3scout v1 release itself.

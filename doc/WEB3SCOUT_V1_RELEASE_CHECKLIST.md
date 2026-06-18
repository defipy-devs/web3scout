# Web3Scout v1.0.0 — Release Checklist

**Status:** Release gate (runs after Phase 1 + Phase 2)
**Predecessor phases:** `PHASE_1_BALANCER_CLAUDE_CODE_HANDOFF.md`, `PHASE_2_CURVE_CLAUDE_CODE_HANDOFF.md`
**Decision context:** DeFiPy v2.2 is on hold. Web3Scout ships as v1 first — it now stands on its own (self-contained, Uni V2/V3 events + state, Balancer/Curve ABIs) and is the stable substrate DeFiPy pins against.

A v1 tag is a one-way credibility door: it signals a stable public surface (`ABILoad`, `ConnectW3`, `FetchToken`, `RetrieveEvents`, the bundled ABIs). Treat this gate as a stability commitment, not a routine bump. Keep it lean — no gold-plating — but don't ship over known crashers.

---

## Pre-flight (must all be true)

- [ ] Phase 1 (Balancer) and Phase 2 (Curve) merged to main.
- [ ] `setup.py` version == `1.0.0`.
- [ ] Full test suite green: `python -m pytest tests/ -v`.
- [ ] `import web3scout` succeeds on a clean venv (web3 6.x). `tests/test_smoke_import.py` covers this — confirm it passes, since a v1 whose top-level import fails is not v1-ready.

## Release-readiness — audit close-out

The April 2026 audit (`WEB3SCOUT_AUDIT.md`) flagged CRITICAL items. Confirm closed before tagging:

- [x] **BUG-1** `convert_hex_bytes_to_string` variable-name crash — fixed (uses `raw` in all branches, clean `else: raise TypeError`). *Verified.*
- [x] **eth_defi dependency** — removed; reorg modules import local `data.block_header`; `setup.py` carries no `eth_defi`. *Verified.*
- [ ] **BUG-2** `FetchToken` `self.token_address` undefined — confirm `tests/test_fetch_token.py` covers it and passes.
- [ ] Any remaining audit BUGs (abi_load import path, etc.) have green regression tests (`test_abi_load.py`, `test_conversion.py`, `test_reorg_monitor.py`, `test_block_header.py`).
- [ ] Known constraint documented, not fixed: web3 pinned `< 7.0` because `abi_load.py` uses `web3._utils.contracts.get_function_info` (removed in web3 7.x). The web3 7.x migration is explicitly **deferred** — note it in the CHANGELOG as a known limitation, don't block v1 on it.

## Docs

- [ ] **README** — add a short line to protocol coverage noting Balancer (V2 Vault + WeightedPool) and Curve (plain StableSwap) ABIs are now bundled and resolvable via `ABILoad(Platform.BALANCER, ...)` / `ABILoad(Platform.CURVE, ...)`. The README currently only shows Uni V2/V3 examples; a one-paragraph mention is enough — no full worked examples required for v1.
- [ ] **CHANGELOG.md** — the repo has none. Create it with a `1.0.0` entry summarizing the road to v1: self-contained (eth_defi removed), Uni V2/V3 events + V2 state reads, Balancer/Curve ABI bundles, the audit bug fixes. Note the web3 6.x ceiling as a known limitation.
- [ ] `LICENSE` + `NOTICE` present and current (Apache-2.0). Already in repo — confirm unchanged.

## Build + verify packaging

- [ ] `python -m build` (sdist + wheel).
- [ ] **Wheel actually contains the new ABIs** (the MANIFEST.in is per-file, so this is the load-bearing check):
  ```
  unzip -l dist/*.whl | grep configs
  ```
  Confirm `balancer/Vault.json`, `balancer/WeightedPool.json`, and `curve/StableSwap.json` all appear. If any is missing, MANIFEST.in is incomplete — fix and rebuild before tagging.
- [ ] **Clean-venv install smoke test** — install the *wheel* (not the source tree, which would mask a packaging gap) and resolve a Balancer + a Curve ABI from the installed package:
  ```
  python -m venv /tmp/w3s_v1 && /tmp/w3s_v1/bin/pip install dist/Web3Scout-1.0.0-*.whl
  /tmp/w3s_v1/bin/python -c "from web3scout.abi.abi_load import ABILoad; from web3scout.enums.platforms_enum import PlatformsEnum as P; \
import json; \
print(ABILoad(P.BALANCER, 'WeightedPool').get_abi_path()); \
print(ABILoad(P.CURVE, 'StableSwap').get_abi_path())"
  ```
  This catches the FileNotFoundError-at-runtime failure mode that an editable/source-tree install would hide.

## Tag + publish

- [ ] `git tag v1.0.0 && git push origin v1.0.0` (git ops are manual — outside the MCP filesystem path).
- [ ] GitHub release `v1.0.0 — Self-contained substrate + Balancer/Curve ABIs`.
- [ ] `twine upload dist/*` to PyPI.
- [ ] Confirm `pip install Web3Scout==1.0.0` from PyPI works in a fresh venv and resolves the new ABIs (repeat the smoke test against the PyPI artifact).

## Post-release

- [ ] DeFiPy v2.2 remains deferred. When it resumes: bump `web3scout >= 0.2.0` → `>= 1.0.0` in the `chain` / `book` / `agentic` extras of `defipy/setup.py`, then proceed per `defipy/doc/v2_2_execution/DEFIPY_V2_2_LIVEPROVIDER_SPEC.md`.

---

*v1 is the "stands on its own" moment: Web3Scout is a self-contained onchain-data substrate with stable enums/ABIs that DeFiPy — and anyone else — can build on. Ship it lean.*

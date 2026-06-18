# Copyright 2023–2025 Ian Moore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Live Balancer & Curve event reads against an Ethereum mainnet RPC.

The endpoint is read from the ETH_RPC_URL environment variable (e.g. set in a
local, git-ignored .env file). The URL is never printed — only its host — so an
API key in the path stays out of your terminal and logs.

Usage:
    # 1) put your endpoint in .env at the repo root (already git-ignored):
    #      ETH_RPC_URL=https://mainnet.infura.io/v3/<your-key>
    # 2) run it (this script auto-loads .env if present):
    #      python examples/live_events.py
    #
    # ...or export it yourself instead of using .env:
    #      export ETH_RPC_URL=https://...
    #      python examples/live_events.py

Requires the supported stack (web3 6.x): `pip install .` into a Python 3.11 venv.
"""

import os
import sys
from collections import Counter
from urllib.parse import urlparse

from web3 import Web3
from web3scout import (
    ABILoad, ConnectW3, RetrieveEvents,
    Platform, JSONContract, EventType, Addr,
)

# Canonical Ethereum mainnet contracts.
CURVE_3POOL = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"   # DAI / USDC / USDT
RPC_ENV_VAR = "ETH_RPC_URL"


def _load_dotenv(path):
    """Minimal .env loader (no python-dotenv dependency). Only fills keys that
    aren't already set, so a real environment variable always wins."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_rpc_url():
    if not os.getenv(RPC_ENV_VAR):
        here = os.path.dirname(os.path.abspath(__file__))
        _load_dotenv(os.path.join(here, "..", ".env"))   # repo-root .env
        _load_dotenv(".env")                             # cwd .env
    url = os.getenv(RPC_ENV_VAR)
    if not url:
        sys.exit(f"{RPC_ENV_VAR} not set — add it to .env or `export {RPC_ENV_VAR}=...`")
    return url


def run(tag, fetch, sample=1):
    """Run one apply() read and print a sample. Catches per-call failures
    (e.g. a transient RPC rate-limit) so one flaky read doesn't abort the demo."""
    try:
        events = fetch()
    except Exception as exc:
        print(f"  {tag:22s} skipped — {type(exc).__name__}: {exc}")
        return
    print(f"  {tag:22s} {len(events):4d} event(s)")
    for i in range(min(sample, len(events))):
        rec = events[i]
        print(f"       e.g. {rec['event']} @ blk {rec['blockNumber']}: {dict(rec['args'])}")


def main():
    url = get_rpc_url()
    print(f"[rpc] {RPC_ENV_VAR} host={urlparse(url).hostname}  (full URL hidden)")

    connect = ConnectW3(url)
    connect.apply()
    if not connect.is_connect():
        sys.exit("[rpc] could not connect")
    w3 = connect.get_w3()
    chain_id = w3.eth.chain_id
    print(f"[rpc] connected  chain_id={chain_id}  latest={w3.eth.block_number}")
    if chain_id != 1:
        sys.exit(f"[rpc] these addresses are Ethereum mainnet; got chain_id {chain_id}")

    latest = w3.eth.block_number - 5   # stay behind head (load-balanced nodes lag)

    # ---- Curve 3pool: swaps + liquidity emitted by the pool ----
    print("\nCurve 3pool (events off the pool):")
    curve = RetrieveEvents(connect, ABILoad(Platform.CURVE, JSONContract.CurveStableSwap), verbose=False)
    run("SWAP",             lambda: curve.apply(EventType.SWAP,             address=CURVE_3POOL, start_block=latest - 3000,  end_block=latest))
    run("ADD_LIQUIDITY",    lambda: curve.apply(EventType.ADD_LIQUIDITY,    address=CURVE_3POOL, start_block=latest - 9000, end_block=latest))
    run("REMOVE_LIQUIDITY", lambda: curve.apply(EventType.REMOVE_LIQUIDITY, address=CURVE_3POOL, start_block=latest - 9000, end_block=latest))

    # ---- Balancer: events live on the canonical Vault, keyed by poolId ----
    print("\nBalancer V2 (events off the Vault):")
    vault_abi = ABILoad(Platform.BALANCER, JSONContract.BalancerVault)
    bal = RetrieveEvents(connect, vault_abi, verbose=False)

    # find a busy poolId from recent Vault swaps so the scoped read has hits
    swap_topic0 = Web3.to_hex(Web3.keccak(text="Swap(bytes32,address,address,uint256,uint256)"))
    recent = w3.eth.get_logs({"address": Web3.to_checksum_address(Addr.BALANCER_V2_VAULT),
                              "topics": [swap_topic0], "fromBlock": latest - 300, "toBlock": latest})
    if recent:
        busiest = Counter(Web3.to_hex(log["topics"][1]) for log in recent).most_common(1)[0][0]
        pool_id = bytes.fromhex(busiest[2:])
        run("SWAP (by poolId)", lambda: bal.apply(EventType.SWAP, address=Addr.BALANCER_V2_VAULT,
                                                  argument_filters={"poolId": pool_id},
                                                  start_block=latest - 300, end_block=latest))
    run("POOL_BALANCE_CHANGED", lambda: bal.apply(EventType.POOL_BALANCE_CHANGED, address=Addr.BALANCER_V2_VAULT,
                                                  start_block=latest - 5000, end_block=latest))

    print("\nDone.")


if __name__ == "__main__":
    main()

"""
Shared test helpers for web3scout tests.

NOTE: web3scout's __init__.py eagerly imports ABILoad which depends on
a private eth_utils API (_abi_to_signature) that was removed in newer
versions. To work around this pre-existing issue, tests that need to
import individual modules use importlib to bypass __init__.py, and
source-level checks read files directly.
"""

import importlib
import importlib.util
import os
import sys

# Base path for web3scout source
PROD_PATH = os.path.join(os.path.dirname(__file__), "..", "python", "prod")


def read_source(relpath: str) -> str:
    """Read a source file relative to python/prod/."""
    with open(os.path.join(PROD_PATH, relpath)) as f:
        return f.read()


def import_module_directly(mod_name: str, file_path: str):
    """Import a single .py file without triggering the package __init__.py.

    This avoids the ABILoad / eth_utils import failure that blocks
    ``import web3scout``.
    """
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod

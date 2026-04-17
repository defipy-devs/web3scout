"""
Tests for web3scout errata fixes (Fixes 6-11 from ERRATA_FIXES.md).

Each test verifies that the specific bug described in the errata
has been corrected.

NOTE: web3scout's __init__.py eagerly imports ABILoad which depends on
a private eth_utils API (_abi_to_signature) that was removed in newer
versions. To work around this pre-existing issue, tests that need to
import individual modules use importlib to bypass __init__.py, and
source-level checks read files directly.
"""

import ast
import importlib
import importlib.util
import os
import sys
import pytest
import pandas as pd
from unittest.mock import MagicMock
from hexbytes import HexBytes

# Base path for web3scout source
_PROD = os.path.join(os.path.dirname(__file__), "..", "python", "prod")


def _read_source(relpath: str) -> str:
    """Read a source file relative to python/prod/."""
    with open(os.path.join(_PROD, relpath)) as f:
        return f.read()


def _import_module_directly(mod_name: str, file_path: str):
    """Import a single .py file without triggering the package __init__.py.

    This avoids the ABILoad / eth_utils import failure that blocks
    `import web3scout`.
    """
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fix 6 — conversion.py: `data` → `raw` variable name
# ---------------------------------------------------------------------------

class TestConversionFix6:
    """Fix 6: convert_hex_bytes_to_string used `data` instead of `raw`."""

    @pytest.fixture(autouse=True)
    def _load_conversion(self):
        path = os.path.join(_PROD, "event", "tools", "conversion.py")
        self.mod = _import_module_directly("_test_conversion", path)
        self.Conversion = self.mod.Conversion

    def test_hexbytes_input(self):
        conv = self.Conversion()
        hb = HexBytes(b"\xde\xad\xbe\xef")
        result = conv.convert_hex_bytes_to_string(hb)
        assert result == "deadbeef"

    def test_bytes_input(self):
        """Before the fix, this raised NameError: name 'data' is not defined."""
        conv = self.Conversion()
        result = conv.convert_hex_bytes_to_string(b"\xca\xfe")
        assert result == "cafe"

    def test_source_uses_raw_not_data(self):
        """Verify the source code no longer references undefined `data` variable."""
        source = _read_source("event/tools/conversion.py")
        # Find the method body and check isinstance calls
        assert "isinstance(data," not in source, "Bug: still using `data` instead of `raw`"

    def test_all_isinstance_branches_use_raw(self):
        """Parse AST to confirm all isinstance() calls in the method use `raw`."""
        source = _read_source("event/tools/conversion.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "convert_hex_bytes_to_string":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and getattr(child.func, 'id', None) == 'isinstance':
                        first_arg = child.args[0]
                        assert isinstance(first_arg, ast.Name) and first_arg.id == "raw", \
                            f"isinstance() should use `raw`, found `{ast.dump(first_arg)}`"


# ---------------------------------------------------------------------------
# Fix 7 — fetch_token.py: error messages and self.token_address → token_address
# ---------------------------------------------------------------------------

class TestFetchTokenFix7:
    """Fix 7: get_token_name / get_token_supply used self.token_address
    (AttributeError) and wrong error messages."""

    def test_get_token_name_source_no_self_token_address(self):
        source = _read_source("token/fetch/fetch_token.py")
        # Extract get_token_name method body
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_name":
                method_source = ast.get_source_segment(source, node)
                assert "self.token_address" not in method_source, \
                    "Bug: get_token_name still uses self.token_address"
                assert "Error fetching name" in method_source, \
                    "Error message should say 'name' not 'symbol'"
                break

    def test_get_token_supply_source_no_self_token_address(self):
        source = _read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_supply":
                method_source = ast.get_source_segment(source, node)
                assert "self.token_address" not in method_source, \
                    "Bug: get_token_supply still uses self.token_address"
                assert "Error fetching supply" in method_source, \
                    "Error message should say 'supply' not 'symbol'"
                break

    def test_get_token_name_handles_exception_gracefully(self):
        """Ensure the except block doesn't raise a secondary AttributeError.

        Before the fix, if name() raised, the except block tried to access
        self.token_address which doesn't exist on FetchToken, causing a
        secondary AttributeError.
        """
        # Import just the module file
        path = os.path.join(_PROD, "token", "fetch", "fetch_token.py")
        # FetchToken imports from web3scout and uniswappy, so we mock those
        # Instead we test via source analysis + the error path logic
        source = _read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_name":
                # Check that the except handler doesn't use self.token_address
                for handler in ast.walk(node):
                    if isinstance(handler, ast.Attribute):
                        if (isinstance(handler.value, ast.Name)
                                and handler.value.id == "self"
                                and handler.attr == "token_address"):
                            pytest.fail("get_token_name except block still uses self.token_address")

    def test_get_token_supply_handles_exception_gracefully(self):
        source = _read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_supply":
                for handler in ast.walk(node):
                    if isinstance(handler, ast.Attribute):
                        if (isinstance(handler.value, ast.Name)
                                and handler.value.id == "self"
                                and handler.attr == "token_address"):
                            pytest.fail("get_token_supply except block still uses self.token_address")


# ---------------------------------------------------------------------------
# Fix 8 — deploy.py: ABILoading → ABILoad
# ---------------------------------------------------------------------------

class TestDeployFix8:
    """Fix 8: deploy_contract referenced ABILoading (undefined) instead of ABILoad."""

    def test_source_uses_abiload_not_abiloading(self):
        source = _read_source("contract/deploy.py")
        assert "ABILoading" not in source, "Bug: still references undefined ABILoading"
        assert "ABILoad()" in source

    def test_ast_no_abiloading_name(self):
        """Parse AST to confirm ABILoading is not referenced anywhere."""
        source = _read_source("contract/deploy.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "ABILoading":
                pytest.fail("AST still contains reference to ABILoading")


# ---------------------------------------------------------------------------
# Fix 9 — abi_load.py: pachira → relative import
# ---------------------------------------------------------------------------

class TestABILoadFix9:
    """Fix 9: get_deployed_contract imported from pachira (external/circular)
    instead of using a relative import."""

    def test_no_pachira_import(self):
        source = _read_source("abi/abi_load.py")
        # Check that no import statement references pachira
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "pachira" in node.module:
                pytest.fail(f"Bug: still imports from pachira: {node.module}")

    def test_uses_relative_import(self):
        source = _read_source("abi/abi_load.py")
        assert "from ..contract.deploy import Deploy" in source


# ---------------------------------------------------------------------------
# Fix 10 — rpc_reorganization_monitor.py: eth_defi → local import
# ---------------------------------------------------------------------------

class TestRPCReorgMonitorFix10:
    """Fix 10: rpc_reorganization_monitor imported BlockHeader from eth_defi."""

    def test_no_eth_defi_import_statement(self):
        source = _read_source("event/tools/rpc_reorganization_monitor.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "eth_defi" in node.module:
                pytest.fail(f"Bug: still imports from eth_defi: {node.module}")

    def test_uses_local_block_header(self):
        source = _read_source("event/tools/rpc_reorganization_monitor.py")
        assert "from ...data.block_header import BlockHeader" in source


# ---------------------------------------------------------------------------
# Fix 11 — reorganization_monitor.py: eth_defi → local import
# ---------------------------------------------------------------------------

class TestReorgMonitorFix11:
    """Fix 11: reorganization_monitor imported BlockHeader from eth_defi."""

    def test_no_eth_defi_import_statement(self):
        source = _read_source("data/reorganization_monitor.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "eth_defi" in node.module:
                pytest.fail(f"Bug: still imports from eth_defi: {node.module}")

    def test_uses_local_block_header(self):
        source = _read_source("data/reorganization_monitor.py")
        assert "from .block_header import BlockHeader, Timestamp" in source


# ---------------------------------------------------------------------------
# Prerequisite — block_header.py: new extracted dataclass
# ---------------------------------------------------------------------------

class TestBlockHeader:
    """Tests for the new block_header.py extracted from eth_defi."""

    @pytest.fixture(autouse=True)
    def _load_block_header(self):
        path = os.path.join(_PROD, "data", "block_header.py")
        self.mod = _import_module_directly("_test_block_header", path)
        self.BlockHeader = self.mod.BlockHeader
        self.Timestamp = self.mod.Timestamp

    def test_timestamp_type_alias(self):
        assert self.Timestamp is int

    def test_create_block_header(self):
        bh = self.BlockHeader(block_number=100, block_hash="0xabc", timestamp=1234567890)
        assert bh.block_number == 100
        assert bh.block_hash == "0xabc"
        assert bh.timestamp == 1234567890

    def test_optional_timestamp(self):
        bh = self.BlockHeader(block_number=1, block_hash="0x1")
        assert bh.timestamp is None

    def test_to_pandas(self):
        from dataclasses import asdict
        data = [
            asdict(self.BlockHeader(block_number=1, block_hash="0xa", timestamp=100)),
            asdict(self.BlockHeader(block_number=2, block_hash="0xb", timestamp=200)),
        ]
        df = self.BlockHeader.to_pandas(data)
        assert len(df) == 2
        assert list(df.columns) == ["block_number", "block_hash", "timestamp"]
        assert df.iloc[0]["block_number"] == 1
        assert df.iloc[1]["block_hash"] == "0xb"

    def test_from_pandas_roundtrip(self):
        from dataclasses import asdict
        data = [
            asdict(self.BlockHeader(block_number=10, block_hash="0xaa", timestamp=1000)),
            asdict(self.BlockHeader(block_number=20, block_hash="0xbb", timestamp=2000)),
        ]
        df = self.BlockHeader.to_pandas(data)
        block_map = self.BlockHeader.from_pandas(df)

        assert 10 in block_map
        assert 20 in block_map
        assert block_map[10].block_hash == "0xaa"
        assert block_map[10].timestamp == 1000
        assert block_map[20].timestamp == 2000

    def test_slots(self):
        bh = self.BlockHeader(block_number=1, block_hash="0x1")
        assert hasattr(type(bh), "__slots__")
        with pytest.raises(AttributeError):
            bh.nonexistent_attr = "should fail"

    def test_file_exists(self):
        path = os.path.join(_PROD, "data", "block_header.py")
        assert os.path.isfile(path), "block_header.py was not created"

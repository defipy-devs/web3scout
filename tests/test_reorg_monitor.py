"""Tests for reorg monitoring imports (Fixes 10-11 from ERRATA_FIXES.md)."""

import ast
import pytest
from conftest import read_source


class TestRPCReorgMonitorImport:
    """Fix 10: rpc_reorganization_monitor imported BlockHeader from eth_defi."""

    def test_no_eth_defi_import(self):
        source = read_source("event/tools/rpc_reorganization_monitor.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "eth_defi" in node.module:
                pytest.fail(f"Bug: still imports from eth_defi: {node.module}")

    def test_uses_local_block_header(self):
        source = read_source("event/tools/rpc_reorganization_monitor.py")
        assert "from ...data.block_header import BlockHeader" in source


class TestReorgMonitorImport:
    """Fix 11: reorganization_monitor imported BlockHeader from eth_defi."""

    def test_no_eth_defi_import(self):
        source = read_source("data/reorganization_monitor.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "eth_defi" in node.module:
                pytest.fail(f"Bug: still imports from eth_defi: {node.module}")

    def test_uses_local_block_header(self):
        source = read_source("data/reorganization_monitor.py")
        assert "from .block_header import BlockHeader, Timestamp" in source

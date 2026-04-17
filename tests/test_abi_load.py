"""Tests for abi/abi_load.py (Fix 9 from ERRATA_FIXES.md)."""

import ast
import pytest
from conftest import read_source


class TestGetDeployedContract:
    """Fix 9: get_deployed_contract imported from pachira (external/circular)
    instead of using a relative import."""

    def test_no_pachira_import(self):
        source = read_source("abi/abi_load.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "pachira" in node.module:
                pytest.fail(f"Bug: still imports from pachira: {node.module}")

    def test_uses_relative_import(self):
        source = read_source("abi/abi_load.py")
        assert "from ..contract.deploy import Deploy" in source

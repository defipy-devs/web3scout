"""Tests for contract/deploy.py (Fix 8 from ERRATA_FIXES.md)."""

import ast
import pytest
from conftest import read_source


class TestDeployContract:
    """Fix 8: deploy_contract referenced ABILoading (undefined) instead of ABILoad."""

    def test_source_uses_abiload_not_abiloading(self):
        source = read_source("contract/deploy.py")
        assert "ABILoading" not in source, "Bug: still references undefined ABILoading"
        assert "ABILoad()" in source

    def test_ast_no_abiloading_name(self):
        """Parse AST to confirm ABILoading is not referenced anywhere."""
        source = read_source("contract/deploy.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "ABILoading":
                pytest.fail("AST still contains reference to ABILoading")

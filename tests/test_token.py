"""Tests for token/token.py (BUG-3 from WEB3SCOUT_AUDIT.md)."""

import ast
import pytest
from conftest import read_source


class TestCreateToken:
    """BUG-3: Token.create_token called bare deploy_contract() which is
    undefined. Should use Deploy().deploy_contract()."""

    def test_uses_deploy_instance(self):
        source = read_source("token/token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "create_token":
                method_source = ast.get_source_segment(source, node)
                assert "Deploy().deploy_contract(" in method_source, \
                    "Bug: create_token should call Deploy().deploy_contract()"
                assert method_source.count("deploy_contract(") == 1
                break
        else:
            pytest.fail("create_token method not found")

    def test_no_bare_deploy_contract_call(self):
        """Ensure there's no bare deploy_contract() call (without Deploy())."""
        source = read_source("token/token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "create_token":
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Name)
                            and child.func.id == "deploy_contract"):
                        pytest.fail("Bug: bare deploy_contract() call — should be Deploy().deploy_contract()")

    def test_deploy_import_exists(self):
        source = read_source("token/token.py")
        assert "from ..contract.deploy import Deploy" in source

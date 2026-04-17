"""Tests for token/fetch/fetch_token.py (Fix 7 from ERRATA_FIXES.md)."""

import ast
import pytest
from conftest import PROD_PATH, read_source


class TestGetTokenNameErrorHandler:
    """Fix 7a: get_token_name used self.token_address (undefined) and
    wrong error message ('symbol' instead of 'name')."""

    def test_no_self_token_address(self):
        source = read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_name":
                method_source = ast.get_source_segment(source, node)
                assert "self.token_address" not in method_source, \
                    "Bug: get_token_name still uses self.token_address"
                assert "Error fetching name" in method_source, \
                    "Error message should say 'name' not 'symbol'"
                break

    def test_except_block_no_attribute_error(self):
        """AST check that except handler doesn't access self.token_address."""
        source = read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_name":
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if (isinstance(child.value, ast.Name)
                                and child.value.id == "self"
                                and child.attr == "token_address"):
                            pytest.fail("get_token_name except block still uses self.token_address")


class TestGetTokenSupplyErrorHandler:
    """Fix 7b: get_token_supply had the same self.token_address bug
    and wrong error message ('symbol' instead of 'supply')."""

    def test_no_self_token_address(self):
        source = read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_supply":
                method_source = ast.get_source_segment(source, node)
                assert "self.token_address" not in method_source, \
                    "Bug: get_token_supply still uses self.token_address"
                assert "Error fetching supply" in method_source, \
                    "Error message should say 'supply' not 'symbol'"
                break

    def test_except_block_no_attribute_error(self):
        source = read_source("token/fetch/fetch_token.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_token_supply":
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if (isinstance(child.value, ast.Name)
                                and child.value.id == "self"
                                and child.attr == "token_address"):
                            pytest.fail("get_token_supply except block still uses self.token_address")

"""Tests for utils/base_utils.py (BUG-6 from WEB3SCOUT_AUDIT.md)."""

import ast
import os
import pytest
from conftest import PROD_PATH, read_source, import_module_directly


class TestFindFreePort:
    """BUG-6a: find_free_port called is_localhost_port_listening()
    without self. prefix."""

    def test_uses_self_prefix(self):
        source = read_source("utils/base_utils.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "find_free_port":
                method_source = ast.get_source_segment(source, node)
                assert "self.is_localhost_port_listening(" in method_source
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Name)
                            and child.func.id == "is_localhost_port_listening"):
                        pytest.fail("Bug: bare is_localhost_port_listening() without self.")
                break
        else:
            pytest.fail("find_free_port method not found")

    def test_runs_without_name_error(self):
        """Actually call find_free_port to confirm no NameError."""
        path = os.path.join(PROD_PATH, "utils", "base_utils.py")
        mod = import_module_directly("_test_base_utils", path)
        utils = mod.BaseUtils()
        port = utils.find_free_port()
        assert isinstance(port, int)
        assert 20_000 <= port < 40_000


class TestShutdownHard:
    """BUG-6b: shutdown_hard had the same missing self. bug."""

    def test_uses_self_prefix(self):
        source = read_source("utils/base_utils.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "shutdown_hard":
                method_source = ast.get_source_segment(source, node)
                assert "self.is_localhost_port_listening(" in method_source
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Name)
                            and child.func.id == "is_localhost_port_listening"):
                        pytest.fail("Bug: bare is_localhost_port_listening() without self.")
                break
        else:
            pytest.fail("shutdown_hard method not found")

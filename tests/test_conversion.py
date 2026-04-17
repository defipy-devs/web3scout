"""Tests for event/tools/conversion.py (Fix 6 from ERRATA_FIXES.md)."""

import ast
import os
import pytest
from hexbytes import HexBytes
from conftest import PROD_PATH, read_source, import_module_directly


class TestConvertHexBytesToString:
    """Fix 6: convert_hex_bytes_to_string used `data` instead of `raw`."""

    @pytest.fixture(autouse=True)
    def _load(self):
        path = os.path.join(PROD_PATH, "event", "tools", "conversion.py")
        mod = import_module_directly("_test_conversion", path)
        self.conv = mod.Conversion()

    def test_hexbytes_input(self):
        result = self.conv.convert_hex_bytes_to_string(HexBytes(b"\xde\xad\xbe\xef"))
        assert result == "deadbeef"

    def test_bytes_input(self):
        """Before the fix, this raised NameError: name 'data' is not defined."""
        result = self.conv.convert_hex_bytes_to_string(b"\xca\xfe")
        assert result == "cafe"

    def test_source_has_no_undefined_data_variable(self):
        source = read_source("event/tools/conversion.py")
        assert "isinstance(data," not in source, "Bug: still using `data` instead of `raw`"

    def test_all_isinstance_branches_use_raw(self):
        """Parse AST to confirm all isinstance() calls in the method use `raw`."""
        source = read_source("event/tools/conversion.py")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "convert_hex_bytes_to_string":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and getattr(child.func, 'id', None) == 'isinstance':
                        first_arg = child.args[0]
                        assert isinstance(first_arg, ast.Name) and first_arg.id == "raw", \
                            f"isinstance() should use `raw`, found `{ast.dump(first_arg)}`"

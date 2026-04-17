"""Tests for data/block_header.py (prerequisite for Fixes 10-11)."""

import os
import pytest
from conftest import PROD_PATH, import_module_directly


@pytest.fixture
def block_header_module():
    path = os.path.join(PROD_PATH, "data", "block_header.py")
    return import_module_directly("_test_block_header", path)


class TestBlockHeader:
    """Tests for the BlockHeader dataclass extracted from eth_defi."""

    def test_file_exists(self):
        path = os.path.join(PROD_PATH, "data", "block_header.py")
        assert os.path.isfile(path), "block_header.py was not created"

    def test_timestamp_type_alias(self, block_header_module):
        assert block_header_module.Timestamp is int

    def test_create(self, block_header_module):
        BH = block_header_module.BlockHeader
        bh = BH(block_number=100, block_hash="0xabc", timestamp=1234567890)
        assert bh.block_number == 100
        assert bh.block_hash == "0xabc"
        assert bh.timestamp == 1234567890

    def test_optional_timestamp(self, block_header_module):
        bh = block_header_module.BlockHeader(block_number=1, block_hash="0x1")
        assert bh.timestamp is None

    def test_to_pandas(self, block_header_module):
        from dataclasses import asdict
        BH = block_header_module.BlockHeader
        data = [
            asdict(BH(block_number=1, block_hash="0xa", timestamp=100)),
            asdict(BH(block_number=2, block_hash="0xb", timestamp=200)),
        ]
        df = BH.to_pandas(data)
        assert len(df) == 2
        assert list(df.columns) == ["block_number", "block_hash", "timestamp"]
        assert df.iloc[0]["block_number"] == 1
        assert df.iloc[1]["block_hash"] == "0xb"

    def test_from_pandas_roundtrip(self, block_header_module):
        from dataclasses import asdict
        BH = block_header_module.BlockHeader
        data = [
            asdict(BH(block_number=10, block_hash="0xaa", timestamp=1000)),
            asdict(BH(block_number=20, block_hash="0xbb", timestamp=2000)),
        ]
        df = BH.to_pandas(data)
        block_map = BH.from_pandas(df)
        assert 10 in block_map
        assert 20 in block_map
        assert block_map[10].block_hash == "0xaa"
        assert block_map[10].timestamp == 1000
        assert block_map[20].timestamp == 2000

    def test_slots(self, block_header_module):
        bh = block_header_module.BlockHeader(block_number=1, block_hash="0x1")
        assert hasattr(type(bh), "__slots__")
        with pytest.raises(AttributeError):
            bh.nonexistent_attr = "should fail"

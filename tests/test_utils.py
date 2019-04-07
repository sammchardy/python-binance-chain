from decimal import Decimal

import pytest

from binance_chain.utils import encode_number, varint_encode


@pytest.mark.parametrize("num, expected", [
    (10, 1000000000),
    (0.08992342, 8992342),
    (Decimal('0.08992342'), 8992342),
    (Decimal('0.99999999'), 99999999),
    (Decimal(10), 1000000000),
])
def test_encode_correct(num, expected):
    assert encode_number(num) == expected


@pytest.mark.parametrize("num, expected", [
    (10,  b'\n'),
    (100, b'd'),
    (64, b'@'),
    (3542, b'\xd6\x1b'),
])
def test_varint_encode_correct(num, expected):
    assert varint_encode(num) == expected

from decimal import Decimal
import binascii

import pytest

from binance_chain.utils.encode_utils import encode_number, varint_encode
from binance_chain.utils.segwit_addr import decode_address, address_from_public_key


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


def test_decode_address():
    expected = binascii.unhexlify(b'7f756b1be93aa2e2fdc3d7cb713abc206f877802')
    assert decode_address('tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5rr') == expected


def test_decode_invalid_address():
    assert decode_address('tbnb10a6kkxlf823w9lwr6l9hzw4uyphcw7qzrud5') is None


def test_address_from_public_key():
    public_key_hex = b'02cce2ee4e37dc8c65d6445c966faf31ebfe578a90695138947ee7cab8ae9a2c08'
    assert address_from_public_key(public_key_hex) == 'tbnb1csdyysz0xqas7dlq754flfsmey8jwaxwgwaqdx'

import math
from decimal import Decimal
from typing import Union


def encode_number(num: Union[float, Decimal]) -> int:
    """Encode number multiply by 1e8 (10^8) and round to int

    :param num: number to encode

    """
    if type(num) == Decimal:
        return int(num * (Decimal(10) ** 8))
    else:
        return int(num * math.pow(10, 8))


def varint_encode(num):
    """Convert number into varint bytes

    :param num: number to encode

    """
    buf = b''
    while True:
        towrite = num & 0x7f
        num >>= 7
        if num:
            buf += bytes(((towrite | 0x80), ))
        else:
            buf += bytes((towrite, ))
            break
    return buf

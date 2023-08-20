# from decimal import Decimal

from collections.abc import Mapping
from contextlib import suppress
from functools import reduce
from re import sub
from typing import Optional

TMoney = float


def parse_money(money: str) -> Optional[TMoney]:
    with suppress(TypeError, ValueError):
        return TMoney(sub(r"[^\d.]", "", money))


def deep_get(dictionary, *keys, default=None):
    """Get item from nested dict"""
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, Mapping) else default,
        keys,
        dictionary,
    )


__all__ = ["parse_money", "deep_get"]

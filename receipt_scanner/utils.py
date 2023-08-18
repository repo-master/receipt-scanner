from re import sub

# from decimal import Decimal

from contextlib import suppress
from typing import Optional


TMoney = float


def parse_money(money: str) -> Optional[TMoney]:
    with suppress(TypeError, ValueError):
        return TMoney(sub(r"[^\d.]", "", money))


__all__ = ["parse_money"]

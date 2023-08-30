# from decimal import Decimal

from base64 import b64encode
from collections.abc import Mapping
from contextlib import suppress
from functools import reduce
from io import BytesIO
from re import sub
from typing import Optional

from PIL import Image

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


def img_to_data_uri(img: Image.Image) -> str:
    with BytesIO() as of:
        img.save(of, format="png")
        b64_data = b64encode(of.getvalue()).decode()
        return 'data:image/png;base64,%s' % b64_data


__all__ = ["parse_money", "deep_get", "img_to_data_uri"]

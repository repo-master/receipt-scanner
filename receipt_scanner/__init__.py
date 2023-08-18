from .pipeline import ScannerPipeline

from .aws import AWSPipeline, get_aws_client

from contextlib import suppress
from typing import Optional


def run(img_file_buffer, scanner_pipeline: ScannerPipeline):
    img_bytearray = img_file_buffer.getvalue()
    response = scanner_pipeline(img_bytearray)
    return response


def parse_money(txt: str) -> Optional[float]:
    with suppress(TypeError):
        return float(txt)

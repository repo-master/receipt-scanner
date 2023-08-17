from .pipeline import ScannerPipeline

from .aws import AWSPipeline, get_aws_client


def run(img_file_buffer, scanner_pipeline: ScannerPipeline):
    img_bytearray = img_file_buffer.getvalue()
    response = scanner_pipeline(img_bytearray)
    return response


def parse_money(txt: str) -> float:
    return None

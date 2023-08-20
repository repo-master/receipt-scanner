from .aws import AWSPipeline, get_aws_client
from .pipeline import ScannerPipeline
from .utils import deep_get, parse_money


def run(img_file_buffer, scanner_pipeline: ScannerPipeline):
    img_bytearray = img_file_buffer.getvalue()
    response = scanner_pipeline(img_bytearray)
    return response

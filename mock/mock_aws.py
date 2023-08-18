from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

import json


class MockAWSConfig(TypedDict):
    analyze_expense_data_file: Path


DEFAULT_TEXTRACT_CONFIG = MockAWSConfig(
    analyze_expense_data_file="mock_data/Full_response.json"
)


class MockAWSClient:
    pass


class MockAWSTextractClient(MockAWSClient):
    def __init__(self, mock_data_config: MockAWSConfig = DEFAULT_TEXTRACT_CONFIG):
        self.mock_config = mock_data_config

    def analyze_expense(self, Document: dict = None):
        with open(self.mock_config["analyze_expense_data_file"]) as f:
            return json.load(f)


def mock_aws_client_factory(service_name: str, **kwargs) -> MockAWSClient:
    match service_name:
        case "textract":
            return MockAWSTextractClient(**kwargs)
    raise ValueError("Unknown service '%s'" % service_name)


@contextmanager
def get_aws_mock_client(service_name: str, **kwargs):
    """
    Returns a mock AWS client for the given service name.

    For unit tests, it is advisable to use the `botocore.stub.Stubber` class to get mock response
    """
    mock_client = mock_aws_client_factory(service_name)
    yield mock_client

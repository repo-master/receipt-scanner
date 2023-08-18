from contextlib import contextmanager

import json


class MockAWSClient:
    pass


class MockAWSTextractClient(MockAWSClient):
    def analyze_expense(self, Document: dict = None):
        with open("Full_response.json") as f:
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

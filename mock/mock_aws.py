from contextlib import contextmanager


class MockAWSClient:
    pass


class MockAWSTextractClient(MockAWSClient):
    def analyze_expense(self, Document: dict = None):
        return {
            "ExpenseDocuments": [
                {
                    "SummaryFields": [],
                    "LineItemGroups": [
                        {
                            "LineItems": {
                                "LineItemExpenseFields": []
                            }
                        }
                    ]
                }
            ]
        }


def mock_aws_client_factory(service_name: str) -> MockAWSClient:
    match service_name:
        case "textract":
            return MockAWSTextractClient()
    raise ValueError("Unknown service '%s'" % service_name)


@contextmanager
def get_aws_mock_client(service_name: str, **kwargs):
    """
    Returns a mock AWS client for the given service name.

    For unit tests, it is advisable to use the `botocore.stub.Stubber` class to get mock response
    """
    mock_client = mock_aws_client_factory(service_name)
    yield mock_client

from .pipeline import ScannerPipeline

from contextlib import contextmanager
from typing import Optional

import boto3
import pandas as pd

from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    region_name: str
    aws_access_key_id: str
    aws_secret_access_key: str


class AWSPipeline(ScannerPipeline):
    def __init__(self, client):
        self.client = client

    def __call__(self, image_data: bytes):
        return self.process_expense_analysis(image_data)

    def process_expense_analysis(self, image_bytes):
        response = self.client.analyze_expense(Document={"Bytes": image_bytes})

        recipt = {}

        recipt["table"] = self.get_table_field(
            response["ExpenseDocuments"][0]["LineItemGroups"]
        )
        recipt["summary"] = self.extract_summary(
            response["ExpenseDocuments"][0]["SummaryFields"],
            len(recipt['table'])
        )
        return recipt

    def get_table_field(self, table_field):
        table = {}
        for line in table_field[0]["LineItems"]:
            row = {}

            for field in line['LineItemExpenseFields']:
                    row[field['Type']['Text']] = field['ValueDetection']['Text']
            table.append(row)

            df = pd.DataFrame(table)
            return df

    def extract_summary(self, summary_field, No_of_items):
        vendor_info = [
            "VENDOR_NAME",
            "VENDOR_ADDRESS",
            "VENDOR_GST_NUMBER",
            "VENDOR_PHONE",
        ]
        recipt_details = [
            "AMOUNT_PAID",
            "INVOICE_RECEIPT_DATE",
            "INVOICE_RECEIPT_ID",
            "SERVICE_CHARGE",
            "SUBTOTAL",
            "TAX",
            "TOTAL",
        ]
        reciver_details = ["TAX_PAYER_ID", "RECEIVER_NAME"]
        OTHER = ["Item Count:", "Qty Count :"]
        response = {}
        response["Vendor"] = {}
        response["Recipt_details"] = {}
        response["Recipt_details"]["OTHER"] = {}
        response["Customer"] = {}

        for item in summary_field:
            if item["Type"]["Text"] in vendor_info:
                response["Vendor"][item["Type"]["Text"]] = item["ValueDetection"][
                    "Text"
                ]
            elif item["Type"]["Text"] in recipt_details:
                response["Recipt_details"][item["Type"]["Text"]] = item[
                    "ValueDetection"
                ]["Text"]
            elif item["Type"]["Text"] in reciver_details:
                response["Customer"][item["Type"]["Text"]] = item["ValueDetection"][
                    "Text"
                ]
            response['Recipt_details']['ITEMS'] = No_of_items

        return response


@contextmanager
def get_aws_client(service_name: str, settings: Optional[AWSSettings] = AWSSettings()):
    """Returns an AWS client from the boto3 package as a self-closing contextmanager"""
    aws_opts = {} if settings is None else settings.dict()
    client = boto3.client(service_name=service_name, **aws_opts)
    yield client
    client.close()
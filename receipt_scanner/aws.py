from contextlib import contextmanager
from typing import Optional

import boto3
import pandas as pd
from pydantic_settings import BaseSettings, SettingsConfigDict

from .pipeline import ScannerPipeline


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    region_name: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None


class AWSPipeline(ScannerPipeline):
    def __init__(self, client):
        self.client = client

    def __call__(self, image_data: bytes):
        return self.process_expense_analysis(image_data)

    def process_expense_analysis(self, image_bytes):
        response = self.client.analyze_expense(Document={"Bytes": image_bytes})

        recipt = {}

        recipt["TABLE"] = self.get_table_field(
            response["ExpenseDocuments"][0]["LineItemGroups"]
        )
        recipt["SUMMARY"] = self.extract_summary(
            response["ExpenseDocuments"][0]["SummaryFields"], len(recipt.get("TABLE", []))
        )
        return recipt

    def get_table_field(self, table_field):
        table = []
        for line in table_field[0]["LineItems"]:
            row = {}

            for field in line["LineItemExpenseFields"]:
                row[field["Type"]["Text"]] = field["ValueDetection"]["Text"]
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
        response = {}
        response["VENDOR"] = {}
        response["RECEIPT_DETAILS"] = {}
        response["CUSTOMER"] = {}

        for item in summary_field:
            if item["Type"]["Text"] in vendor_info:
                response["VENDOR"][item["Type"]["Text"]] = item["ValueDetection"][
                    "Text"
                ]
            elif item["Type"]["Text"] in recipt_details:
                response["RECEIPT_DETAILS"][item["Type"]["Text"]] = item[
                    "ValueDetection"
                ]["Text"]
            elif item["Type"]["Text"] in reciver_details:
                response["CUSTOMER"][item["Type"]["Text"]] = item["ValueDetection"][
                    "Text"
                ]
            response["RECEIPT_DETAILS"]["ITEMS"] = No_of_items

        return response


@contextmanager
def get_aws_client(service_name: str, settings: Optional[AWSSettings] = AWSSettings()):
    """Returns an AWS client from the boto3 package as a self-closing contextmanager"""
    aws_opts = {} if settings is None else settings.dict()
    client = boto3.client(service_name=service_name, **aws_opts)
    yield client
    client.close()

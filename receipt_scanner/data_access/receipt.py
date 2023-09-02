from typing import List, Optional, Tuple, Union

import pandas as pd
from fuzzywuzzy import process
from sqlalchemy.orm import Session

from ..models import Receipt
from ..utils import deep_get


def filter_receipts(
    receipts: List[Receipt],
    search_query: Optional[str] = None,
    limit_results: Optional[int] = None,
) -> Tuple[List[Receipt], List[str]]:
    _filter_by_keys = ["vendor", "invoice_id", "scan_date", "total", "invoice_date", "category"]
    """Which keys are used to search the receipts"""

    if search_query is None:
        # Default sort by scan date
        receipts.sort(key=lambda r: r.time_scanned, reverse=True)
        return receipts, None

    # Split query by whitespace
    search_query = search_query.split()

    def receipt_obj_processor(obj: Union[Receipt, str, list]):
        if isinstance(obj, list):
            return ' '.join(obj)
        if isinstance(obj, Receipt):
            summ = receipt_summary_obj(obj)
            return {key: summ[key] for key in _filter_by_keys if summ[key] is not None}
        return obj
    match_ratios = process.extractBests(
        search_query,
        receipts,
        processor=receipt_obj_processor,
        limit=10,
        score_cutoff=50
    )
    return [r for r, _ in match_ratios], search_query


def receipt_summary_obj(receipt: Receipt):
    return {
        "id": receipt.receipt_id,
        "scan_date": receipt.time_scanned,
        "vendor": deep_get(receipt.summary, "VENDOR", "VENDOR_NAME", default="N/A"),
        "total": deep_get(receipt.summary, "RECEIPT_DETAILS", "TOTAL", default="N/A"),
        "item_count": deep_get(
            receipt.summary, "RECEIPT_DETAILS", "ITEMS", default="N/A"
        ),
        "invoice_id": deep_get(
            receipt.summary,
            "RECEIPT_DETAILS",
            "INVOICE_RECEIPT_ID",
            default="N/A",
        ),
        "invoice_date": deep_get(
            receipt.summary,
            "RECEIPT_DETAILS",
            "INVOICE_RECEIPT_DATE",
            default="N/A",
        ),
        "category": receipt.category,
    }


def query_get_receipts(
    sess: Session, search_query: str = None, limit_results: int = None
) -> Tuple[List, List[str]]:
    receipts: List[Receipt] = sess.query(Receipt).all()
    receipts, query_str = filter_receipts(receipts, search_query, limit_results)

    return [receipt_summary_obj(rcpt) for rcpt in receipts], query_str


def insert_add_receipt(sess: Session, result: dict, img_file_buffer: bytes) -> Receipt:
    table_data: Optional[pd.DataFrame] = result["TABLE"]
    item_list = []
    if table_data is not None:
        item_list = table_data.to_dict()

    new_receipt = Receipt(summary=result["SUMMARY"], item_listing=item_list, image_data=img_file_buffer)
    sess.add(new_receipt)
    sess.commit()
    sess.flush()
    sess.refresh(new_receipt)

    return new_receipt

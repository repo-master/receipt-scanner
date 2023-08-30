import difflib
from heapq import nlargest
from typing import List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from ..models import Receipt
from ..utils import deep_get


def filter_receipts(
    receipts: List[Receipt],
    search_query: Optional[str] = None,
    limit_results: Optional[int] = None,
) -> Tuple[List[Receipt], List[str]]:
    if search_query is None:
        return receipts, None

    search_query = search_query.split(" ")

    def receipt_to_string(r: Receipt):
        return "; ".join(
            [
                deep_get(r.summary, "VENDOR", "VENDOR_NAME"),
                deep_get(r.summary, "RECEIPT_DETAILS", "INVOICE_RECEIPT_ID"),
            ]
        )

    cutoff = 0.1
    result = []
    s = difflib.SequenceMatcher()

    for q in search_query:
        s.set_seq2(q.lower())
        for x in receipts:
            s.set_seq1(receipt_to_string(x).lower())
            if s.ratio() >= cutoff:
                result.append((s.ratio(), x))

    # Move the best scorers to head of list
    if limit_results is not None:
        result = nlargest(limit_results, result)
    result.sort(key=lambda r: r[0], reverse=True)
    # Strip scores for the best n matches
    return set(x for score, x in result), search_query


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

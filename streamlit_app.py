import logging
import streamlit as st
import pandas as pd

import receipt_scanner
from receipt_scanner import deep_get, get_aws_client

from typing import MutableMapping, Any, Optional, List
from streamlit.type_util import Key
from streamlit.connections import SQLConnection

from streamlit_echarts import st_echarts

from mock import get_aws_mock_client


LOGGER = logging.getLogger(__name__)


_aws_use_mock: bool = deep_get(st.secrets, "aws_client", "use_mock_client", default=False)
DEFAULT_AWS_CLIENT_FN = get_aws_mock_client if _aws_use_mock else get_aws_client


def insert_new_receipt(result, save_db: SQLConnection):
    from receipt_scanner.models import Receipt
    with save_db.session as sess:
        table_data: Optional[pd.DataFrame] = result['table']
        item_list = []
        if table_data is not None:
            item_list = table_data.to_dict()

        rcpt = Receipt(
            summary=result['summary'],
            item_listing=item_list
        )
        sess.add(rcpt)
        sess.commit()


def image_upload_handler(
    img_file_buffer,
    save_db: SQLConnection,
    result_state_key: str,
    session_state: MutableMapping[Key, Any] = st.session_state,
    get_aws_client_fn=DEFAULT_AWS_CLIENT_FN,
):
    with st.spinner("Processing..."):
        with get_aws_client_fn("textract") as aws_client:
            result = receipt_scanner.run(
                img_file_buffer, receipt_scanner.AWSPipeline(aws_client)
            )
            session_state[result_state_key] = result
            insert_new_receipt(result, save_db)


receipt_db_conn = st.experimental_connection("receipts_db", type="sql")
# TODO: Make it run only ONCE! This will run every time the page is rendered
with receipt_db_conn.session as sess:
    from receipt_scanner.db.base import Base

    # Import all model classes so that they are added to the Base
    import receipt_scanner.models

    Base.metadata.create_all(receipt_db_conn._instance)


# UI start
# Make note that "magic" output is enabled so the below strings will output to the UI

if _aws_use_mock:
    "Note: Using Mock AWS client for processing image"


"# Receipt scanner"

scanner_tab, statistics_tab = st.tabs(["Scanner", "Statistics"])

with scanner_tab:
    "Upload a receipt image to OCR, Analyze and parse it"

    if "cam_disabled" not in st.session_state:
        st.session_state["cam_disabled"] = True

    if "receipt_data" not in st.session_state:
        st.session_state["receipt_data"] = None

    file_tab, cam_tab, history_tab = st.tabs(["Upload", "Camera", "History"])

    with file_tab:
        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg", "gif", "webp", "bmp"],
            accept_multiple_files=False,
            help="Select a receipt image to upload",
        )
        if uploaded_file is not None:
            image_upload_handler(uploaded_file, receipt_db_conn, "receipt_data")

    with cam_tab:

        def _toggle_cam():
            st.session_state["cam_disabled"] = not st.session_state["cam_disabled"]

        st.button(
            "Enable camera" if st.session_state["cam_disabled"] else "Disable camera",
            on_click=_toggle_cam,
        )
        captured_image = st.camera_input(
            "Scan with Camera", disabled=st.session_state.cam_disabled
        )

        if captured_image is not None:
            image_upload_handler(captured_image, receipt_db_conn, "receipt_data")

    with history_tab:
        from receipt_scanner.models import Receipt

        with receipt_db_conn.session as session:
            all_receipts: Optional[List[Receipt]] = session.query(Receipt).all()
            if all_receipts is None or len(all_receipts) == 0:
                st.write("No saved receipts found")
            else:
                receipts = [{
                    "id": rcpt.receipt_id,
                    "scan_date": rcpt.time_scanned,
                    "vendor": deep_get(rcpt.summary, "Vendor", "VENDOR_NAME"),
                    "total": deep_get(rcpt.summary, "Recipt_details", "TOTAL"),
                    "item_count": len(rcpt.item_listing),
                    "invoice_id": deep_get(rcpt.summary, "Recipt_details", "INVOICE_RECEIPT_ID"),
                    "invoice_date": deep_get(rcpt.summary, "Recipt_details", "INVOICE_RECEIPT_DATE"),
                    "category": rcpt.category,
                } for rcpt in all_receipts]
                st.dataframe(receipts)

    "## Results"

    def more_item_details(item_data: Optional[pd.DataFrame], summary_data):
        item_dataset = []
        if item_data is not None:
            item_dataset = [
                {"name": itm["ITEM"], "value": itm["PRICE"]}
                for idx, itm in item_data.iterrows()
            ]

        if summary_data is not None and "Recipt_details" in summary_data:
            bill_summary = summary_data["Recipt_details"]
            tax_paid = receipt_scanner.parse_money(bill_summary["TAX"])
            if tax_paid is not None:
                item_dataset.append({"name": "Tax", "value": tax_paid})

        options = {
            "title": {
                "text": "Price breakdown",
                "subtext": "Item-wise price",
                "left": "center",
            },
            "tooltip": {"trigger": "item"},
            "legend": {
                "orient": "vertical",
                "left": "left",
            },
            "series": [
                {
                    "name": "Item",
                    "type": "pie",
                    "radius": "50%",
                    "data": item_dataset,
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)",
                        }
                    },
                },
            ],
        }
        st_echarts(
            options=options,
            height="600px",
            theme="dark",  # FIXME: See https://github.com/streamlit/streamlit/issues/5009
        )

    def show_scan_results():
        # NOTE: *DO NOT DELETE* the strings placed here, they are "Magic" outputs
        receipt_data = st.session_state.get("receipt_data")

        item_data = None
        summary_data = None

        if receipt_data is None:
            "Upload an image or select from history to view results"
        else:
            item_data = receipt_data["table"]
            summary_data = receipt_data["summary"]

            img_preview_col, summary_col = st.columns(2)

            with img_preview_col:
                "Scanned image"
                if uploaded_file is not None:
                    st.image(uploaded_file, caption="Uploaded image", width=300)

            with summary_col:
                "Summary"
                if summary_data is not None:
                    st.json(summary_data)

            with st.container():
                "Item list"

                st.dataframe(data=item_data)

                if item_data is None or item_data.empty:
                    "No items detected"

                with st.expander("More details"):
                    more_item_details(item_data, summary_data)

    show_scan_results()


with statistics_tab:
    "Receipt statistics"

import logging
from datetime import datetime
from typing import Any, List, MutableMapping, Optional

import pandas as pd
from streamlit_echarts import st_echarts

import receipt_scanner
import streamlit as st
from mock import get_aws_mock_client
from receipt_scanner import deep_get, get_aws_client
from receipt_scanner.models import Receipt
from streamlit.connections import SQLConnection
from streamlit.type_util import Key

LOGGER = logging.getLogger(__name__)

RECEIPT_RESULT_DATA_KEY = "receipt_result_data"


if "cam_disabled" not in st.session_state:
    # Camera is off by default (privacy)
    st.session_state["cam_disabled"] = True

if RECEIPT_RESULT_DATA_KEY not in st.session_state:
    # What amounts to the results of the Receipt data (image, summary, items)
    st.session_state[RECEIPT_RESULT_DATA_KEY] = None


_aws_use_mock: bool = deep_get(
    st.secrets, "aws_client", "use_mock_client", default=False
)
DEFAULT_AWS_CLIENT_FN = get_aws_mock_client if _aws_use_mock else get_aws_client


def insert_new_receipt(result, img_file_buffer, save_db: SQLConnection):
    with save_db.session as sess:
        table_data: Optional[pd.DataFrame] = result["TABLE"]
        item_list = []
        if table_data is not None:
            item_list = table_data.to_dict()

        rcpt = Receipt(summary=result["SUMMARY"], item_listing=item_list, image_data=img_file_buffer)
        sess.add(rcpt)
        sess.commit()


def image_upload_handler(
    img_file_buffer,
    save_db: SQLConnection,
    result_state_key: str,
    session_state: MutableMapping[Key, Any] = st.session_state,
    get_aws_client_fn=DEFAULT_AWS_CLIENT_FN,
):
    LOGGER.info("Process: %s", img_file_buffer)
    if img_file_buffer is None:
        return
    with st.spinner("Processing..."):
        with get_aws_client_fn("textract") as aws_client:
            # Perform document analysis and get the result
            result = receipt_scanner.run(
                img_file_buffer, receipt_scanner.AWSPipeline(aws_client)
            )
            # Set the result state (to display to the user)
            session_state[result_state_key] = {
                "SUMMARY": result["SUMMARY"],
                "TABLE": result["TABLE"],
                "IMAGE": img_file_buffer,
            }
            insert_new_receipt(result, img_file_buffer.read(), save_db)


def show_history_item(
    item: Receipt,
    result_state_key: str,
    session_state: MutableMapping[Key, Any] = st.session_state,
):
    session_state[result_state_key] = {
        "SUMMARY": item.summary,
        "TABLE": pd.DataFrame(item.item_listing),
        "IMAGE": item.image_data,
    }


receipt_db_conn = st.experimental_connection("receipts_db", type="sql")
# TODO: Make it run only ONCE! This will run every time the page is rendered
with receipt_db_conn.session as sess:
    # Import all model classes so that they are added to the Base
    import receipt_scanner.models
    from receipt_scanner.db.base import Base

    Base.metadata.create_all(receipt_db_conn._instance)


# UI start
# Make note that "magic" output is enabled so the below strings will output to the UI

if _aws_use_mock:
    "Note: Using Mock AWS client for processing image"


"# Receipt scanner"

scanner_tab, statistics_tab = st.tabs(["Scanner", "Statistics"])

with scanner_tab:
    "Upload a receipt image to OCR, Analyze and parse it"

    file_tab, cam_tab, history_tab = st.tabs(["Upload", "Camera", "History"])

    with file_tab:
        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg", "gif", "webp", "bmp"],
            accept_multiple_files=False,
            help="Select a receipt image to upload",
        )

        st.button(
            "Process",
            key="btn_process_upload",
            type="secondary",
            disabled=uploaded_file is None,
            on_click=image_upload_handler,
            args=(uploaded_file, receipt_db_conn, RECEIPT_RESULT_DATA_KEY),
        )

    with cam_tab:

        def _toggle_cam():
            st.session_state["cam_disabled"] = not st.session_state["cam_disabled"]

        st.button(
            "Enable camera" if st.session_state["cam_disabled"] else "Disable camera",
            on_click=_toggle_cam,
        )
        captured_image = st.camera_input(
            "Scan with Camera",
            disabled=st.session_state.cam_disabled,
        )
        st.button(
            "Process",
            key="btn_process_camera",
            type="secondary",
            disabled=captured_image is None,
            on_click=image_upload_handler,
            args=(captured_image, receipt_db_conn, RECEIPT_RESULT_DATA_KEY),
        )

    with history_tab:
        selected_receipt_item = None

        def _get_receipt_label(receipt_item):
            return "%s - %s" % (
                receipt_item["scan_date"].strftime("%c"),
                receipt_item["vendor"],
            )

        with receipt_db_conn.session as session:
            all_receipts: Optional[List[Receipt]] = session.query(Receipt).all()
            if all_receipts is None or len(all_receipts) == 0:
                st.write("No saved receipts found")
            else:
                receipts = pd.DataFrame(
                    [
                        {
                            "id": rcpt.receipt_id,
                            "scan_date": rcpt.time_scanned,
                            "vendor": deep_get(rcpt.summary, "VENDOR", "VENDOR_NAME"),
                            "total": deep_get(rcpt.summary, "RECEIPT_DETAILS", "TOTAL"),
                            "item_count": deep_get(
                                rcpt.summary, "RECEIPT_DETAILS", "ITEMS"
                            ),
                            "invoice_id": deep_get(
                                rcpt.summary, "RECEIPT_DETAILS", "INVOICE_RECEIPT_ID"
                            ),
                            "invoice_date": deep_get(
                                rcpt.summary, "RECEIPT_DETAILS", "INVOICE_RECEIPT_DATE"
                            ),
                            "category": rcpt.category,
                        }
                        for rcpt in all_receipts
                    ]
                )  # .set_index("id")

                st.dataframe(receipts, hide_index=True)
                selected_receipt_item = st.selectbox(
                    ":receipt: Show result",
                    receipts.index,
                    placeholder="Item",
                    format_func=lambda item: _get_receipt_label(receipts.loc[item]),
                )

            def _process_history_item():
                selected_receipt_obj = None
                if selected_receipt_item is not None:
                    selected_receipt_obj = all_receipts[selected_receipt_item]
                if selected_receipt_obj is not None:
                    show_history_item(selected_receipt_obj, RECEIPT_RESULT_DATA_KEY)

            st.button(
                "Show",
                key="btn_process_history",
                type="secondary",
                disabled=selected_receipt_item is None,
                on_click=_process_history_item,
            )

    "## Results"

    def more_item_details(item_data: Optional[pd.DataFrame], summary_data):
        """Shows Pie chart to show per-item breakdown chart"""
        item_dataset = []
        if item_data is not None:
            item_dataset = [
                {"name": itm["ITEM"], "value": itm["PRICE"]}
                for idx, itm in item_data.iterrows()
            ]

        if summary_data is not None and "RECEIPT_DETAILS" in summary_data:
            try:
                bill_summary = summary_data["RECEIPT_DETAILS"]
                tax_paid = receipt_scanner.parse_money(bill_summary.get("TAX"))
                if tax_paid is not None:
                    item_dataset.append({"name": "Tax", "value": tax_paid})
            except KeyError:
                pass

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
        receipt_data = st.session_state.get(RECEIPT_RESULT_DATA_KEY)

        item_data = None
        summary_data = None

        if receipt_data is None:
            "Upload an image or select from history to view results"
        else:
            item_data = receipt_data["TABLE"]
            summary_data = receipt_data["SUMMARY"]
            scanned_image = receipt_data["IMAGE"]

            img_preview_col, summary_col = st.columns(2)

            with img_preview_col:
                "Scanned image"
                if scanned_image is None:
                    "Image not available"
                else:
                    st.image(scanned_image, caption="Uploaded image", width=300)

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

    with receipt_db_conn.session as session:
        all_receipts: Optional[List[Receipt]] = session.query(Receipt).all()

        receipts = pd.DataFrame(
            [
                {
                    "id": rcpt.receipt_id,
                    "scan_date": rcpt.time_scanned,
                    "vendor": deep_get(rcpt.summary, "VENDOR", "VENDOR_NAME"),
                    "total": receipt_scanner.parse_money(deep_get(rcpt.summary, "RECEIPT_DETAILS", "TOTAL")),
                    "item_count": deep_get(rcpt.summary, "RECEIPT_DETAILS", "ITEMS"),
                    "invoice_id": deep_get(
                        rcpt.summary, "RECEIPT_DETAILS", "INVOICE_RECEIPT_ID"
                    ),
                    "invoice_date": deep_get(
                        rcpt.summary, "RECEIPT_DETAILS", "INVOICE_RECEIPT_DATE"
                    ),
                    "category": rcpt.category,
                }
                for rcpt in all_receipts
            ]
        )

        if not receipts.empty:
            this_year_receipts = receipts[receipts["scan_date"].dt.year == datetime.now().year]
            this_year_monthwise = this_year_receipts.groupby(receipts["scan_date"].map(lambda r: r.strftime("%Y %B")))

            "### Number of receipts (by month)"
            _this_year_monthwise_count_df = pd.DataFrame([
                {
                    "month": month_name,
                    "count": len(df)
                }
                for month_name, df in this_year_monthwise
            ]).set_index("month")
            st.bar_chart(_this_year_monthwise_count_df)

            "### Total expenditure (by month)"
            _this_year_monthwise_price_df = pd.DataFrame([
                {
                    "month": month_name,
                    "bill_total": df["total"].sum()
                }
                for month_name, df in this_year_monthwise
            ]).set_index("month")
            st.bar_chart(_this_year_monthwise_price_df)

            "### Number of receipts (by vendor)"
            st.bar_chart(receipts["vendor"].value_counts())

            # options = {
            #     "title": {
            #         "text": "Price breakdown",
            #         "subtext": "Item-wise price",
            #         "left": "center",
            #     },
            #     "tooltip": {"trigger": "item"},
            #     "legend": {
            #         "orient": "vertical",
            #         "left": "left",
            #     },
            #     "series": [
            #         {
            #             "name": "Item",
            #             "type": "pie",
            #             "radius": "50%",
            #             "data": item_dataset,
            #             "emphasis": {
            #                 "itemStyle": {
            #                     "shadowBlur": 10,
            #                     "shadowOffsetX": 0,
            #                     "shadowColor": "rgba(0, 0, 0, 0.5)",
            #                 }
            #             },
            #         },
            #     ],
            # }

            # st_echarts(
            #     options=options,
            #     height="600px",
            #     theme="dark",  # FIXME (same theme issue as above)
            # )

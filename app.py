import streamlit as st
import numpy as np
import pandas as pd

import receipt_scanner

from typing import MutableMapping, Any
from streamlit.type_util import Key

from streamlit_echarts import st_echarts


def image_upload_handler(
    img_file_buffer,
    result_state_key: str,
    session_state: MutableMapping[Key, Any] = st.session_state,
):
    with st.spinner('Processing...'):
        with receipt_scanner.get_aws_client("textract") as aws_client:
            result = receipt_scanner.run(
                img_file_buffer, receipt_scanner.AWSPipeline(aws_client)
            )
            session_state[result_state_key] = result


# UI start

"# Receipt scanner"
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
        image_upload_handler(uploaded_file, "receipt_data")

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
        image_upload_handler(captured_image, "receipt_data")


def more_item_details(item_data, summary_data):
    item_dataset = []
    if item_data is not None:
        item_dataset = [
            {"name": itm["ITEM"], "value": itm["PRICE"]} for idx, itm in item_data.iterrows()
        ]

    if summary_data is not None and "Recipt_details" in summary_data:
        bill_summary = summary_data["Recipt_details"]
        tax_paid = receipt_scanner.parse_money(bill_summary["TAX"])
        if tax_paid is not None:
            item_dataset.append({
                "name": "Tax",
                "value": tax_paid
            })

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
    )


def show_scan_results():
    # NOTE: *DO NOT DELETE* the strings placed here, they are "Magic" outputs
    receipt_data = st.session_state.get("receipt_data")

    item_data = None
    summary_data = None

    if receipt_data is not None:
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

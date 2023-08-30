from contextlib import suppress
from functools import lru_cache, partial
from typing import List, Optional, Union
from urllib.request import urlopen

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import ALL, Input, Output, State, callback, dash_table, dcc, html
from dash_iconify import DashIconify
from PIL import Image, UnidentifiedImageError

from receipt_scanner.data_access.receipt import (query_get_receipts,
                                                 receipt_summary_obj)
from receipt_scanner.db import DBConnectionFactory
from receipt_scanner.models import Receipt
from receipt_scanner.utils import img_to_data_uri, parse_money

CONN_URL = "sqlite:///receipts.test.db"
VALID_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]


def make_receipt_card(
    receipt_obj: Receipt, highlights: Optional[Union[str, List[str]]] = None
):
    receipt_id = receipt_obj["id"]
    item_price = receipt_obj["total"]
    invoice_id = receipt_obj["invoice_id"]

    return dmc.Card(
        children=[
            dcc.Store(
                id={"type": "receipt-view-id", "index": receipt_id}, data=receipt_id
            ),
            dmc.CardSection(
                dmc.Image(
                    src="https://upload.wikimedia.org/wikipedia/commons/0/0b/ReceiptSwiss.jpg",
                    height=160,
                )
            ),
            dmc.Text(
                dmc.Highlight(receipt_obj["vendor"], highlight=highlights),
                weight=500,
                mt="md",
                mb="xs",
            ),
            dmc.Group(
                [
                    dmc.Text(dmc.Highlight(invoice_id, highlight=highlights)),
                    dmc.Badge(
                        item_price,
                        color="red",
                        variant="light",
                    )
                    if item_price
                    else dmc.ThemeIcon(
                        DashIconify(icon="mdi:currency-usd-off", width=16),
                        radius="xl",
                        color="red",
                        size=20,
                    ),
                ],
                position="apart",
                mb="xs",
            ),
            dmc.List(
                icon=dmc.ThemeIcon(
                    DashIconify(icon="radix-icons:check-circled", width=12),
                    radius="sm",
                    color="teal",
                    size=18,
                ),
                children=[
                    dmc.ListItem(
                        dmc.Tooltip(
                            label="Scanned date",
                            withArrow=True,
                            children=dmc.Text(
                                receipt_obj["scan_date"].strftime("%c"),
                                size="sm",
                                color="dimmed",
                            ),
                        ),
                        icon=dmc.ThemeIcon(
                            DashIconify(icon="mdi:calendar-clock-outline", width=12),
                            radius="sm",
                            color="teal",
                            size=18,
                        ),
                    ),
                    dmc.ListItem(
                        dmc.Text(
                            f'{receipt_obj["item_count"]} items',
                            size="sm",
                            color="dimmed",
                        ),
                        icon=dmc.ThemeIcon(
                            DashIconify(icon="mdi:format-list-numbered", width=12),
                            radius="sm",
                            color="teal",
                            size=18,
                        ),
                    ),
                ],
            ),
            dmc.Button(
                "View details",
                id={"type": "receipt-view-details-btn", "index": receipt_id},
                variant="light",
                color="blue",
                fullWidth=True,
                mt="md",
                radius="md",
                n_clicks=0,
            ),
        ],
        withBorder=True,
        shadow="sm",
        radius="md",
        style={"width": 350},
    )


def make_receipt_modal(receipt_id: int):
    with DBConnectionFactory.connection(CONN_URL) as conn:
        with conn() as sess:
            receipt: Optional[Receipt] = sess.query(Receipt).get(receipt_id)
            if receipt is None:
                return "Selected receipt does not have any data"

            item_list = receipt.item_listing
            receipt_summary = receipt.summary

            # Some extracted summary to display
            rec_details = receipt_summary_obj(receipt)

            prod_items = pd.DataFrame(
                item_list,
                columns=["ITEM", "UNIT_PRICE", "QUANTITY", "PRICE"],
            )
            _prod_view = prod_items[["ITEM", "UNIT_PRICE", "QUANTITY", "PRICE"]]
            if receipt_summary is not None and "RECEIPT_DETAILS" in receipt_summary:
                try:
                    bill_summary = receipt_summary["RECEIPT_DETAILS"]
                    tax_paid = parse_money(bill_summary.get("TAX"))
                    if tax_paid is not None:
                        _prod_view = pd.concat(
                            [
                                _prod_view,
                                pd.DataFrame([{"ITEM": "Tax", "PRICE": tax_paid}]),
                            ]
                        )
                except KeyError:
                    pass

            return [
                html.Div(
                    [
                        dmc.Text("Details", size="lg", weight=700),
                        dmc.Text(f'Vendor: {rec_details["vendor"]}'),
                        dmc.Text(f'Scanned on: {rec_details["scan_date"]}'),
                        dmc.Text(f'Total: {rec_details["total"]}'),
                        dmc.Text(f'Invoice number: {rec_details["invoice_id"]}'),
                    ]
                ),
                dmc.Text("Items", size="lg", weight=700, mt="sm"),
                (
                    dmc.Text("No items present")
                    if _prod_view.empty
                    else dash_table.DataTable(
                        data=_prod_view.to_dict(orient="records"),
                        tooltip_data=[
                            {
                                column: {
                                    "value": f"{value} ({column})",
                                    "type": "markdown",
                                }
                                for column, value in row.items()
                            }
                            for row in _prod_view.to_dict(orient="records")
                        ],
                        page_size=5,
                        style_cell={
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "maxWidth": 0,
                        },
                        style_table={"overflowX": "auto"},
                    )
                ),
                dcc.Graph(
                    figure=px.pie(
                        _prod_view,
                        values="PRICE",
                        names="ITEM",
                        title="Item summary",
                    )
                )
                if not _prod_view.empty
                else None,
            ]
    return "Unknown error occurred"


def get_results(query=None):
    receipt_results = []
    search_highlights = query

    # TODO: Move connection to Dash app's management somehow
    with DBConnectionFactory.connection(CONN_URL) as conn:
        with conn() as sess:
            receipt_results, search_highlights = query_get_receipts(sess, query)

    if len(receipt_results) == 0:
        return "No results"

    return dmc.SimpleGrid(
        cols=1,
        spacing="sm",
        breakpoints=[
            {"minWidth": "sm", "cols": 2, "spacing": "sm"},
            {"minWidth": "lg", "cols": 3, "spacing": "md"},
            {"minWidth": "xl", "cols": None},
        ],
        children=list(
            map(
                partial(make_receipt_card, highlights=search_highlights),
                receipt_results,
            )
        ),
    )


def upload_button():
    return [
        dmc.Menu(
            [
                dmc.MenuTarget(
                    dmc.ActionIcon(
                        DashIconify(icon="mdi:camera-plus", width=32),
                        size=72,
                        variant="gradient",
                        radius="50%",
                        color="lime",
                        n_clicks=0,
                    ),
                ),
                dmc.MenuDropdown(
                    [
                        dmc.MenuItem(
                            "Camera",
                            id="btn-upload-camera",
                            n_clicks=0,
                            icon=DashIconify(icon="mdi:camera-outline"),
                        ),
                        dmc.MenuItem(
                            "Upload file",
                            id="btn-upload-file",
                            n_clicks=0,
                            icon=DashIconify(icon="mdi:file-upload-outline"),
                        ),
                    ]
                ),
            ],
            transition="slide-up",
            transitionDuration=150,
        ),
        dmc.Modal(
            title=dmc.Text("Upload image", size="xl", weight=700),
            id="modal-upload-image-file",
            size="lg",
            zIndex=10000,
            closeOnClickOutside=False,
            overlayBlur=4,
            opened=True,
            children=[
                dmc.Button(
                    "Scan",
                    id="file-upload-perform-scan",
                    disabled=True,
                    color="blue",
                    mb="md",
                    variant="gradient",
                    rightIcon=DashIconify(icon="mdi:send-variant-outline"),
                ),
                dcc.Upload(
                    [
                        dmc.Center(
                            [
                                dmc.Text("Drag and Drop or"),
                                dmc.Space(w="xs"),
                                dmc.Text("Select a File", underline=True),
                            ]
                        ),
                        dcc.Loading(
                            html.Div(id="output-data-file-upload"), type="circle"
                        ),
                    ],
                    id="upload-file-data",
                    multiple=False,
                    accept=["image/*"],
                    style={
                        "cursor": "pointer",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "padding": "2em",
                    },
                ),
            ],
        ),
    ]


def receipt_gallery():
    return [
        dmc.TextInput(
            id="filter-results",
            placeholder="Filter receipts",
            icon=DashIconify(icon="mdi:filter-outline"),
            debounce=500,
            my="sm",
            rightSection=dmc.ActionIcon(
                DashIconify(icon="mdi:close", width=24),
                id="clear-filter-results",
                size=24,
                variant="transparent",
                color="gray",
                n_clicks=0,
                disabled=True,
            ),
        ),
        html.Span(id="result-message"),
        html.Div(id="result-output"),
        dmc.Affix(upload_button(), position={"bottom": 20, "right": 20}),
        dmc.Modal(
            title=dmc.Text("Receipt details", size="xl", weight=700),
            id="modal-view-receipt",
            size="lg",
            zIndex=10000,
            opened=False,
        ),
    ]


def receipt_statistics():
    pass
    # if not receipts.empty:
    #     this_year_receipts = receipts[
    #         receipts["scan_date"].dt.year == datetime.now().year
    #     ]
    #     this_year_monthwise = this_year_receipts.groupby(
    #         receipts["scan_date"].map(lambda r: r.strftime("%Y %B"))
    #     )

    #     _this_year_monthwise_count_df = pd.DataFrame(
    #         [
    #             {"month": month_name, "count": len(df)}
    #             for month_name, df in this_year_monthwise
    #         ]
    #     ).set_index("month")

    # return html.Div(
    #     [
    #         html.H4("Number of receipts (by month)"),
    #         dcc.Graph(
    #             id="graph",
    #             figure=px.bar(_this_year_monthwise_count_df, barmode="group"),
    #         ),
    #         dcc.Graph(
    #             id="graph",
    #             figure=px.bar(receipts["vendor"].value_counts(), barmode="group"),
    #         ),
    #     ]
    # )


""" Enable page and set as root """

dash.register_page(__name__, path="/")


""" Main layout """

layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Receipt Gallery", value="gallery"),
                dmc.Tab("Statistics", value="statistics"),
                dmc.Tab(
                    "Settings",
                    value="settings",
                    ml="auto",
                    rightSection=DashIconify(icon="mdi:gear-outline", width=16),
                ),
            ]
        ),
        dmc.TabsPanel(receipt_gallery(), value="gallery"),
        dmc.TabsPanel(receipt_statistics(), value="statistics"),
        dmc.TabsPanel("Settings tab content", value="settings"),
    ],
    color="red",
    orientation="horizontal",
    value="gallery",
)


""" API / callbacks """


@lru_cache()
def watermark_image() -> Optional[Image.Image]:
    with suppress(UnidentifiedImageError):
        return Image.open("./assets/images/watermark.png")


def validate_image_gen_preview(file_url: str) -> Optional[str]:
    try:
        with urlopen(file_url) as response:
            img: Image.Image = Image.open(response.file)
            img.thumbnail(size=(480, 480), resample=Image.Resampling.LANCZOS)
            watermark = watermark_image()
            if watermark is not None:
                center = (
                    (img.width // 2) - (watermark.width // 2),
                    (img.height // 2) - (watermark.height // 2),
                )
                img.paste(watermark, center, watermark)
            return img_to_data_uri(img)
    except UnidentifiedImageError:
        return


@callback(
    [
        Output("result-output", "children"),
        Output("result-message", "children"),
    ],
    Input("filter-results", "value"),
)
def search_submit(search_input):
    if search_input and len(search_input) > 0:
        result_output = get_results(search_input)
        return result_output, 'Filtered results for "%s"' % search_input
    return get_results(), None


@callback(
    Output("filter-results", "value"),
    Input("clear-filter-results", "n_clicks"),
)
def search_filter_clear(n_clicks):
    if n_clicks:
        return ""


@callback(
    Output("clear-filter-results", "disabled"),
    Input("filter-results", "value"),
    prevent_initial_call=True,
)
def search_filter_clear_disable(search_input):
    if search_input is None:
        return True
    return len(search_input) == 0


@callback(
    [
        Output("modal-view-receipt", "opened"),
        Output({"type": "receipt-view-details-btn", "index": ALL}, "n_clicks"),
        Output("modal-view-receipt", "children"),
    ],
    Input({"type": "receipt-view-details-btn", "index": ALL}, "n_clicks"),
    State("modal-view-receipt", "opened"),
    State({"type": "receipt-view-id", "index": ALL}, "data"),
    prevent_initial_call=True,
)
def toggle_item_view_modal(n_clicks, opened, receipt_ids):
    if any(n_clicks):
        receipt_data = None
        try:
            sel_idx = n_clicks.index(1)
            sel_receipt = receipt_ids[sel_idx]
            receipt_data = make_receipt_modal(sel_receipt)
        except ValueError:
            pass

        return not opened, [0 for _ in n_clicks], receipt_data
    return opened, n_clicks, None


# Upload file modal toggle
@callback(
    Output("modal-upload-image-file", "opened"),
    Input("btn-upload-file", "n_clicks"),
    State("modal-upload-image-file", "opened"),
)
def toggle_file_upload_modal(n_clicks, is_open):
    if n_clicks:
        return True
    return is_open


# File upload callback
@callback(
    [
        Output("output-data-file-upload", "children"),
        Output("file-upload-perform-scan", "disabled"),
    ],
    [Input("upload-file-data", "contents")],
    [State("upload-file-data", "filename")],
)
def update_output(f_content, f_name):
    if f_content is not None:
        img_encoded = None
        try:
            img_encoded = validate_image_gen_preview(f_content)
        except Exception as ex:
            # TODO: Log
            return dmc.Group(
                [
                    dmc.Text(
                        "File could not be parsed due to an error:",
                        color="red",
                        align="center",
                    ),
                    dmc.Text(type(ex).__name__, color="dimmed", align="center"),
                ]
            ), True

        if img_encoded is not None:
            # Image is valid
            return dmc.Image(src=img_encoded, alt=f_name), False

        # Error (not valid image)
        accepted_types = ", ".join(VALID_IMAGE_EXTENSIONS)
        return dmc.Group(
            [
                dmc.Text(
                    "File is not a valid image (could not be parsed).",
                    color="red",
                    align="center",
                ),
                dmc.Text(
                    "Valid image types are: %s, etc." % accepted_types,
                    color="dimmed",
                    align="center",
                ),
            ]
        ), True

    return None, True

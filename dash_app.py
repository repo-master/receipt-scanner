import time
from datetime import datetime

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import (Dash, Input, Output, State, callback, clientside_callback,
                  dash_table, dcc, html, page_container)

INDEX_PAGE = open("templates/index_blank.template.html").read()

app = Dash(
    __name__,
    use_pages=True,
    index_string=INDEX_PAGE,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
        "/assets/dash-fixes.css",
    ],
    external_scripts=[
        # "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        # "/assets/main.js",
    ],
    suppress_callback_exceptions=True,
)

app.layout = dmc.MantineProvider(
    inherit=True,
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=[
        dcc.Location(id="page-location"),
        dmc.LoadingOverlay(dbc.Container(page_container)),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0")

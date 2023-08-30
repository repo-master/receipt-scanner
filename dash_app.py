import time
from datetime import datetime

import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash import (Dash, Input, Output, State, callback, clientside_callback,
                  dash_table, dcc, html, page_container)
from flask import Flask

from receipt_scanner.api import routes
from receipt_scanner.db.flask_db import app_db

INDEX_PAGE = open("templates/index_blank.template.html").read()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receipts.test.db"

    dash_app = Dash(
        __name__,
        server=app,
        use_pages=True,
        index_string=INDEX_PAGE,
        external_stylesheets=[
            "/assets/dash-fixes.css",
        ],
        external_scripts=[],
        suppress_callback_exceptions=True,
    )

    dash_app.layout = dmc.MantineProvider(
        inherit=True,
        withGlobalStyles=True,
        withNormalizeCSS=True,
        children=[
            dcc.Location(id="page-location"),
            dmc.LoadingOverlay(dmc.Container(page_container, fluid=True)),
        ],
    )

    app_db.init_app(app)
    routes.init_app(app)

    with app.app_context():
        app_db.create_all()

    return app


if __name__ == "__main__":
    app: Flask = create_app()
    app.run(debug=False, host="0.0.0.0", load_dotenv=True)

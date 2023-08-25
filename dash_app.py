from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import (Dash, Input, Output, State, callback, clientside_callback,
                  dash_table, dcc, html)

import dash_elements

INDEX_PAGE = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <link rel="manifest" href="./assets/manifest.json" />
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        <!--[if IE]><script>
        alert("Dash v2.7+ does not support Internet Explorer. Please use a newer browser.");
        </script><![endif]-->
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


receipts = pd.read_json("receipts.json")
receipts["scan_date"] = pd.to_datetime(receipts["scan_date"])


app = Dash(
    __name__,
    index_string=INDEX_PAGE,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    external_scripts=["/assets/main.js"],
    suppress_callback_exceptions=True
)

app.layout = html.Div(
    [
        dash_elements.AppNavbar(),
        dbc.Tabs(
            id="app-tabs",
            children=[
                dbc.Tab(label="Receipts", tab_id="tab-scanner"),
                dbc.Tab(label="Statistics", tab_id="tab-stats"),
            ],
        ),
        html.Div(id="app-tabs-content"),
        html.Div(id='hidden-div', style={'display': 'none'})
    ]
)


@callback(
    Output("app-tabs-content", "children"),
    Input("app-tabs", "active_tab"),
)
def switch_app_tab_render_content(tab):
    if tab == "tab-scanner":
        return html.Div(
            [
                dcc.Upload([
                    'Drag and Drop or ',
                    html.A('Select a File')
                ], id='upload-data', style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center'
                })
                # dash_table.DataTable(data=receipts.to_dict("records"), page_size=10),
            ]
        )
    elif tab == "tab-stats":
        if not receipts.empty:
            this_year_receipts = receipts[
                receipts["scan_date"].dt.year == datetime.now().year
            ]
            this_year_monthwise = this_year_receipts.groupby(
                receipts["scan_date"].map(lambda r: r.strftime("%Y %B"))
            )

            _this_year_monthwise_count_df = pd.DataFrame(
                [
                    {"month": month_name, "count": len(df)}
                    for month_name, df in this_year_monthwise
                ]
            ).set_index("month")

        return html.Div(
            [
                html.H4("Number of receipts (by month)"),
                dcc.Graph(
                    id="graph",
                    figure=px.bar(_this_year_monthwise_count_df, barmode="group"),
                ),
                dcc.Graph(
                    id="graph",
                    figure=px.bar(receipts["vendor"].value_counts(), barmode="group"),
                ),
            ]
        )


@app.callback(Output('hidden-div', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(f_content, f_name):
    if f_content is not None:
        pass


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

from datetime import datetime

import pandas as pd
import plotly.express as px
import sd_material_ui
from dash import Dash, Input, Output, callback, dash_table, dcc, html

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
receipts['scan_date'] = pd.to_datetime(receipts['scan_date'])


app = Dash(__name__, index_string=INDEX_PAGE)


app.layout = sd_material_ui.Paper(
    [
        html.H3("Receipt Scanner"),
        dcc.Tabs(
            id="tabs-example-graph",
            value="tab-1-example-graph",
            children=[
                dcc.Tab(label="Scanner", value="tab-1-example-graph"),
                dcc.Tab(label="Statistics", value="tab-2-example-graph"),
            ],
        ),
        html.Div(id="tabs-content-example-graph"),
    ]
)


@callback(
    Output("tabs-content-example-graph", "children"),
    Input("tabs-example-graph", "value"),
)
def render_content(tab):
    if tab == "tab-1-example-graph":
        return html.Div(
            [
                html.H3("Receipt history"),
                dash_table.DataTable(data=receipts.to_dict("records"), page_size=10),
            ]
        )
    elif tab == "tab-2-example-graph":
        if not receipts.empty:
            this_year_receipts = receipts[receipts["scan_date"].dt.year == datetime.now().year]
            this_year_monthwise = this_year_receipts.groupby(receipts["scan_date"].map(lambda r: r.strftime("%Y %B")))

            _this_year_monthwise_count_df = pd.DataFrame([
                {
                    "month": month_name,
                    "count": len(df)
                }
                for month_name, df in this_year_monthwise
            ]).set_index("month")

        return html.Div(
            [
                html.H3("Receipt statistics"),
                html.H4("Number of receipts (by month)"),
                dcc.Graph(id="graph", figure=px.bar(_this_year_monthwise_count_df, barmode="group")),
                dcc.Graph(id="graph", figure=px.bar(receipts["vendor"].value_counts(), barmode="group"))
            ]
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

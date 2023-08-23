import pandas as pd
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


df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv"
)


app = Dash(__name__, index_string=INDEX_PAGE)


app.layout = sd_material_ui.Paper(
    [
        html.H3("Receipt Scanner"),
        dcc.Tabs(
            id="tabs-example-graph",
            value="tab-1-example-graph",
            children=[
                dcc.Tab(label="Upload", value="tab-1-example-graph"),
                dcc.Tab(label="Camera", value="tab-2-example-graph"),
                dcc.Tab(label="History", value="tab-3-example-graph"),
            ],
        ),
        html.Div(id="tabs-content-example-graph"),
        dash_table.DataTable(data=df.to_dict("records"), page_size=10),
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
                html.H3("Tab content 1"),
            ]
        )
    elif tab == "tab-2-example-graph":
        return html.Div(
            [
                html.H3("Tab content 2"),
            ]
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

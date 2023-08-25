import dash_bootstrap_components as dbc
from dash import html


def SearchBar():
    return dbc.Row(
        [
            dbc.InputGroup(
                [
                    dbc.Input(type="search", placeholder="Search receipts"),
                    dbc.Button(
                        html.I(className="bi bi-search"), color="secondary", n_clicks=0
                    ),
                ]
            )
        ],
        className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
        align="center",
    )


def AppNavbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            # dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                            dbc.Col(html.I(className="bi bi-receipt")),
                            dbc.Col(dbc.NavbarBrand("Receipt Scanner", className="ms-2")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                dbc.Col(dbc.Button(children=html.I(className="bi bi-camera"))),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    SearchBar(),
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
    )

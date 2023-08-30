# import dash_bootstrap_components as dbc
# from dash import Input, Output, callback, dcc, html


# def UploadImageModal():
#     return html.Div([
#         dbc.Modal(
#             id="upload-image-modal",
#             is_open=True,
#             children=[
#                 dbc.ModalHeader(dbc.ModalTitle("Scan Receipt")),
#                 dbc.ModalBody(
#                     [
#                         dcc.Upload(
#                             [
#                                 dcc.Loading(
#                                     html.Div(id="output-data-upload"), type="circle"
#                                 ),
#                                 html.Div(
#                                     html.Div(
#                                         [
#                                             "Drag and Drop or ",
#                                             html.Span(
#                                                 "Select a File",
#                                                 className="text-decoration-underline",
#                                             ),
#                                         ]
#                                     ),
#                                     className="d-flex justify-content-center text-center",
#                                 ),
#                             ],
#                             id="upload-data",
#                             className="p-4",
#                             style={
#                                 "cursor": "pointer",
#                                 "borderWidth": "1px",
#                                 "borderStyle": "dashed",
#                                 "borderRadius": "5px",
#                             },
#                         )
#                     ]
#                 ),
#                 dbc.ModalFooter(
#                     html.Button(
#                         "Cancel",
#                         id="close-scan-modal-dialog",
#                         type="button",
#                         className="btn btn-secondary ms-auto",
#                         disable_n_clicks=True,
#                         **{"data-bs-dismiss": "modal"}
#                     )
#                 ),
#             ],
#         )
#     ])


# def SearchBar():
#     return dbc.Row(
#         [
#             dbc.Form(
#                 children=dbc.InputGroup(
#                     [
#                         dbc.Input(
#                             type="search",
#                             id="search-query",
#                             placeholder="Search receipts",
#                         ),
#                         dbc.Button(
#                             html.I(className="bi bi-search"),
#                             color="secondary",
#                             type="submit",
#                         ),
#                     ],
#                 ),
#                 id="search-form",
#                 n_submit=0,
#             )
#         ],
#         className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
#         align="center",
#     )


# def AppNavbar():
#     return dbc.Navbar(
#         dbc.Container(
#             [
#                 html.A(
#                     dbc.Row(
#                         [
#                             dbc.Col(html.I(className="bi bi-receipt")),
#                             dbc.Col(
#                                 dbc.NavbarBrand("Receipt Scanner", className="ms-2")
#                             ),
#                         ],
#                         align="center",
#                         className="g-0",
#                     ),
#                     href="/",
#                     style={"textDecoration": "none"},
#                 ),
#                 dbc.Col(
#                     html.Button(
#                         children=html.I(className="bi bi-camera"),
#                         disable_n_clicks=True,
#                         type="button",
#                         id="open-scan-modal",
#                         className="btn btn-primary",
#                         **{"data-bs-toggle": "modal", "data-bs-target": "#upload-image-modal"}
#                     )
#                 ),
#                 dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
#                 dbc.Collapse(
#                     SearchBar(),
#                     id="navbar-collapse",
#                     is_open=False,
#                     navbar=True,
#                 ),
#             ],
#         ),
#         color="dark",
#         dark=True,
#     )

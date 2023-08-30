from flask import Flask
from flask_restful import Api

from .resources import ReceiptThumbnail


def init_app(app: Flask):
    api = Api(app, prefix="/receipt")
    api.add_resource(ReceiptThumbnail, "/<int:receipt_id>/thumbnail")

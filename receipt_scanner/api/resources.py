from io import BytesIO
from typing import Optional

from flask import abort, send_file
from flask_restful import Resource

from ..db.flask_db import app_db
from ..models import Receipt


class ReceiptThumbnail(Resource):
    def get(self, receipt_id: int):
        buff = BytesIO()
        buff.name = "thumbnail.png"

        receipt: Optional[Receipt] = app_db.session.query(Receipt).get(receipt_id)
        if receipt is None:
            return abort(404, "Selected receipt does not have any data")

        if receipt.image_data is None:
            return abort(204)

        buff.write(receipt.image_data)
        buff.seek(0)
        return send_file(buff, download_name=buff.name)

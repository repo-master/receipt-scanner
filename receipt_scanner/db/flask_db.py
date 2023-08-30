from flask_sqlalchemy import SQLAlchemy

from .base import metadata

app_db = SQLAlchemy(metadata=metadata)

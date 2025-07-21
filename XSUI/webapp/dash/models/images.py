"""
Models for storing WAXS and GIWAXS images in a database using Flask-SQLAlchemy.

These models define the structure of the database tables for storing image data, including metadata and image attributes.
"""

import sqlalchemy as sa
from XSUI.webapp.dash.models import models_db


class ImageWAXS(models_db.Model):
    __tablename__ = "waxs_images"

    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.String(255), nullable=False, unique=True)
    image_data = sa.Column(sa.LargeBinary, nullable=False)

    def __repr__(self):
        return f"<ImageWAXS id={self.id} filename={self.filename}>"

    def __init__(self, filename, image_data):
        self.filename = filename
        self.image_data = image_data


class ImageCalibrant(models_db.Model):
    __tablename__ = "calibrant_images"

    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.String(255), nullable=False, unique=True)
    image_data = sa.Column(sa.LargeBinary, nullable=False)

    def __repr__(self):
        return f"<ImageCalibrant id={self.id} filename={self.filename}>"

    def __init__(self, filename, image_data):
        self.filename = filename
        self.image_data = image_data


class ImageGIWAXS(models_db.Model):
    __tablename__ = "giwaxs_images"

    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.String(255), nullable=False, unique=True)

    angle_incidence = sa.Column(sa.Float, nullable=False)
    angle_tilt = sa.Column(sa.Float, nullable=False)
    orientation = sa.Column(sa.Integer, nullable=True)

    image_data = sa.Column(sa.LargeBinary, nullable=False)

    def __repr__(self):
        return f"<ImageGIWAXS id={self.id} filename={self.filename}>"

    def __init__(self, filename, image_data):
        self.filename = filename
        self.image_data = image_data

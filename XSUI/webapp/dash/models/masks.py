"""
Models for storing the masks used in WAXS and GIWAXS imaging in a database using Flask-SQLAlchemy.
"""

import numpy as np
import sqlalchemy as sa
import sqlalchemy.orm as orm
from XSUI.webapp.dash.models import models_db
from typing import List


class DetectorMask(models_db.Model):
    """
    A model for storing detector masks used in WAXS and GIWAXS imaging.

    Model data is typically generated through `pyFAI` registered detectors.
    """

    __tablename__ = "detector_masks"

    id = sa.Column(sa.Integer, primary_key=True)
    detector_mask = sa.Column(sa.LargeBinary, nullable=False)
    detector_name = sa.Column(sa.String(50), nullable=False)

    def __repr__(self):
        return f"<DetectorMask id={self.id} detector_name={self.detector_name}>"

    def __init__(self, detector_name, detector_mask: np.ndarray):
        self.detector_name = detector_name
        self.detector_mask = detector_mask.dumps()


class CustomMask(models_db.Model):
    """
    A model for storing custom masks used in WAXS and GIWAXS imaging.

    Typically generated through the `Plotly` interactive figure interface.
    """

    __tablename__ = "custom_masks"

    id = sa.Column(sa.Integer, primary_key=True)
    mask_data = sa.Column(sa.LargeBinary, nullable=False)

    def __repr__(self):
        return f"<CustomMask id={self.id}>"

    def __init__(self, mask_data: np.ndarray):
        self.mask_data = mask_data.dumps()


# Create an association table for CompositeMask and CustomMask
class Base(orm.DeclarativeBase):
    pass


association_table = sa.Table(
    "composite_mask_associations",
    Base.metadata,
    sa.Column("composite_mask_id", sa.ForeignKey("composite_masks.id")),
    sa.Column("custom_mask_id", sa.ForeignKey("custom_masks.id")),
)


class CompositeMask(models_db.Model):
    """
    A model for storing composite masks, which are combinations of multiple masks.

    Useful for complex masking scenarios in WAXS and GIWAXS imaging.
    """

    __tablename__ = "composite_masks"

    id = sa.Column(sa.Integer, primary_key=True)
    detector_mask: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("detector_masks.id")
    )
    custom_masks: orm.Mapped[List["CustomMask"]] = orm.relationship(
        secondary=association_table
    )

    def __repr__(self):
        return f"<CompositeMask id={self.id}>"

    def __init__(self, mask_data: np.ndarray):
        self.mask_data = mask_data.dumps()

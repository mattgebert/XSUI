from XSUI.webapp.fastapi.models.images import (
    ImageWAXS,
    ImageGIWAXS,
    ImageCalibrant,
    ImageBase,
)
from XSUI.webapp.fastapi.models.masks import (
    DetectorMask,
    CustomMask,
    CompositeMask,
    MaskBase,
)
import sqlalchemy.orm as orm

models_list_all = [
    ImageWAXS,
    ImageGIWAXS,
    ImageCalibrant,
    DetectorMask,
    CustomMask,
    CompositeMask,
]

bases_list_all: list[type[orm.DeclarativeBase]] = [
    ImageBase,
    MaskBase,
]

from XSUI.webapp.dash.main import db as models_db

from XSUI.webapp.dash.models.images import ImageWAXS, ImageGIWAXS, ImageCalibrant
from XSUI.webapp.dash.models.masks import DetectorMask, CustomMask, CompositeMask


models_list_all = [
    ImageWAXS,
    ImageGIWAXS,
    ImageCalibrant,
    DetectorMask,
    CustomMask,
    CompositeMask,
]

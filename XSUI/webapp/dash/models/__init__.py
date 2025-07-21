from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from XSUI.webapp.dash.models.images import ImageWAXS, ImageGIWAXS
from XSUI.webapp.dash.models.masks import DetectorMask, CustomMask
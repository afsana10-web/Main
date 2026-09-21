# InspectionImage, ImageCategory and ImageQuality are defined in inspection.py
# (they are tightly coupled to Inspection). Re-exported here so the module
# layout matches the documented structure and other code can do
# `from app.models.image import InspectionImage`.
from app.models.inspection import InspectionImage, ImageCategory, ImageQuality  # noqa: F401

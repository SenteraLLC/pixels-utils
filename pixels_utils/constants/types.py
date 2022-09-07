# from numpy.typing import ArrayLike
from typing import NewType

from requests import Response

STAC_crop = NewType("STAC_crop", Response)
STAC_info = NewType("STAC_info", Response)
STAC_statistics = NewType("STAC_statistics", Response)

# STAC_crop_data = NewType("STAC_crop_data", ArrayLike)
# STAC_crop_metadata = NewType("STAC_crop_metadata", Dict)

from typing import NewType

from requests.models import Response

STAC_crop = NewType("STAC_crop", Response)
STAC_info = NewType("STAC_info", Response)
STAC_statistics = NewType("STAC_statistics", Response)

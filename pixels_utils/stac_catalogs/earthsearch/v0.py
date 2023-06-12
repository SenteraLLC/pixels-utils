from enum import Enum, auto

from pixels_utils.stac_catalogs.earthsearch import AutoDashNameEnum

EARTHSEARCH_URL = "https://earth-search.aws.element84.com/v0"
EARTHSEARCH_SCENE_URL = f"{EARTHSEARCH_URL}" "collections/{collection}/items/{id}"


class EarthSearchCollections(AutoDashNameEnum):
    sentinel_s2_l2a = auto()
    sentinel_s2_l1c = auto()
    sentinel_s2_l2a_cogs = auto()
    landsat_8_l1_c1 = auto()

    def equals(self, string):
        if isinstance(string, Enum):
            string = string.name
        return self.name == string

from enum import Enum, auto

from pixels_utils.stac_catalogs.earthsearch import AutoDashNameEnum

EARTHSEARCH_URL = "https://earth-search.aws.element84.com/v1"
EARTHSEARCH_SCENE_URL = "{EARTHSEARCH_URL}" "collections/{collection}/items/{sceneid}"


class EarthSearchCollections(AutoDashNameEnum):
    cop_dem_glo_30 = auto()
    naip = auto()
    sentinel_2_l2a = auto()
    sentinel_2_l1c = auto()
    landsat_c2_l2 = auto()
    cop_dem_glo_90 = auto()
    sentinel_1_grd = auto()

    def equals(self, string):
        if isinstance(string, Enum):
            string = string.name
        return self.name == string

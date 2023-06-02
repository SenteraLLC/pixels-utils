from enum import Enum, auto

ELEMENT84_SEARCH_URL = "https://earth-search.aws.element84.com/v1"

ELEMENT84_SCENE_COLLECTION_URL = "https://earth-search.aws.element84.com/v1/" "collections/{collection}/items/{sceneid}"


class AutoDashNameEnum(Enum):
    def __init__(self, value):
        self._name_ = self._name_.replace("_", "-")
        self._value_ = value


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

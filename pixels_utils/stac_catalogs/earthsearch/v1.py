from enum import Enum, IntEnum, auto

from spyndex import indices as spyndex_indices

from pixels_utils.stac_catalogs._expression_helper import Expression, Expressions
from pixels_utils.stac_catalogs.earthsearch import AutoDashNameEnum
from pixels_utils.stac_metadata import STACMetaData

EARTHSEARCH_URL = "https://earth-search.aws.element84.com/v1"
EARTHSEARCH_COLLECTION_URL = f"{EARTHSEARCH_URL}" "/collections/{collection}"
EARTHSEARCH_SCENE_URL = f"{EARTHSEARCH_URL}" "/collections/{collection}/items/{id}"


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


def expression_from_collection(
    collection: EarthSearchCollections = EarthSearchCollections.sentinel_2_l2a, spectral_index: str = "NDVI"
) -> Expression:
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    assert set(Expression(spyndex_object=spyndex_indices[spectral_index]).assets).issubset(
        set(stac_metadata.asset_names)
    ), f'Assets for spectral index "{spectral_index}" are not available in collection "{collection}".'
    assert (
        spectral_index in spyndex_indices.keys()
    ), f"{spectral_index} is not a valid spectral index (must be available via spyndex.indices)."
    return Expression(spyndex_object=spyndex_indices["NDVI"])


def expressions_from_collection(
    collection: EarthSearchCollections = EarthSearchCollections.sentinel_2_l2a,
) -> Expressions:
    # Get list of assets in collection and filter spyndex_bands by collection assets
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    return Expressions(
        **{
            spectral_index: (
                Expression(spyndex_object=spyndex_indices[spectral_index])
                if set(Expression(spyndex_object=spyndex_indices[spectral_index]).assets).issubset(
                    set(stac_metadata.asset_names)
                )
                else None
            )
            for spectral_index in spyndex_indices
        }
    )


class SCL(IntEnum):
    """Sentinel-2 L2A Scene Classification classes.

    From https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm
    """

    NO_DATA = 0
    SATURATED_OR_DEFECTIVE = 1
    CAST_SHADOWS = 2
    CLOUD_SHADOWS = 3
    VEGETATION = 4
    BARE_SOIL = 5
    WATER = 6
    UNCLASSIFIED = 7
    CLOUD_MEDIUM_PROBABILITY = 8
    CLOUD_HIGH_PROBABILITY = 9
    THIN_CIRRUS = 10
    SNOW_OR_ICE = 11


SCL_GROUP_ARABLE = [SCL.VEGETATION, SCL.BARE_SOIL]
SCL_GROUP_CLOUDS = [
    SCL.CAST_SHADOWS,
    SCL.CLOUD_SHADOWS,
    SCL.CLOUD_MEDIUM_PROBABILITY,
    SCL.CLOUD_HIGH_PROBABILITY,
    SCL.THIN_CIRRUS,
]

from enum import Enum, IntEnum, auto
from functools import cached_property

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

    @cached_property
    def _version(self):
        return "v1"


def expression_from_collection(
    collection: EarthSearchCollections = EarthSearchCollections.sentinel_2_l2a, spectral_index: str = "NDVI"
) -> Expression:
    """
    Returns an Expression object for a given collection and spectral index.

    See `spyndex_indices` for a list of available spectral indices.

    Args:
        collection (EarthSearchCollections, optional): The collection that spectral_index should be tailored to.
        Defaults to EarthSearchCollections.sentinel_2_l2a.

        spectral_index (str, optional): The acronym for the spectral index you'd like returned as an Expression. Must be
        a spectral index available via spyndex. Defaults to "NDVI".

    Returns:
        Expression: Teh tailored Expression object.
    """
    assert collection._version == "v1", (
        f"The `collection` and `expression_from_collection()` function versions do not match ({collection._version} vs "
        f'v1). Ensure both the "{collection}" and expression_from_collection() function are imported from the same '
        "version of `pixels_utils.stac_catalogs.earthsearch`."
    )
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    # TODO: stac_metadata.parse_asset_bands("eo:bands", return_dataframe=True) for support of EarthSearch v0
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
    """
    Returns an Expressions object for a given collection containing all available spectral indices.

    Args:
        collection (EarthSearchCollections, optional): The collection to generate Expressions for. Defaults to
        EarthSearchCollections.sentinel_2_l2a.

    Returns:
        Expressions: The Expressions object containing all available spectral indices for the given collection.
    """
    assert collection._version == "v1", (
        f"The `collection` and `expression_from_collection()` function versions do not match ({collection._version} vs "
        f'v1). Ensure both the "{collection}" and expression_from_collection() function are imported from the same '
        "version of `pixels_utils.stac_catalogs.earthsearch`."
    )
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

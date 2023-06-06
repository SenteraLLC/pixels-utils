from enum import IntEnum

# ASSETS_TCI = ("visual",)
ASSETS_TCI = ("B04", "B03", "B02")
ASSETS_OVERVIEW = ("overview",)
ASSETS_MSI = (
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B09",
    "B11",
    "B12",
)
ASSETS_SPECIAL = ("AOT", "SCL", "WVP")
SENTINEL2_UKIS = ("B02", "B03", "B04", "B08", "B11", "B12")

EXPRESSION_NDVI = "(B08-B04)/(B08+B04)"
EXPRESSION_NDRE = "(B08-B05)/(B08+B05)"


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

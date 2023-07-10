from dataclasses import dataclass
from enum import IntEnum


class Sentinel2_SCL(IntEnum):
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


@dataclass
class Sentinel2_SCL_Group:
    """Sentinel-2 L2A Scene Classification groups."""

    ARABLE = [Sentinel2_SCL.VEGETATION, Sentinel2_SCL.BARE_SOIL]
    CLOUDS = [
        Sentinel2_SCL.CAST_SHADOWS,
        Sentinel2_SCL.CLOUD_SHADOWS,
        Sentinel2_SCL.CLOUD_MEDIUM_PROBABILITY,
        Sentinel2_SCL.CLOUD_HIGH_PROBABILITY,
        Sentinel2_SCL.THIN_CIRRUS,
    ]

from typing import Any, Dict, Tuple, Union

from geo_utils.vector import geojson_to_shapely, validate_geojson
from geo_utils.vector._geojson import GEOJSON_GEOMETRY_KEYS, VALID_GEOJSON_GEOM_TYPES
from geo_utils.vector._shapely import VALID_SHAPELY_GEOM_TYPES

from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

Bounds = Tuple[float, float, float, float]


def _bounds_from_geojson_or_geometry(geometry: Any) -> Bounds:
    """Gets the bounding box of the given geometry, which can be a GeoJSON object, a shapely object, or a WKT string."""
    if isinstance(geometry, VALID_SHAPELY_GEOM_TYPES):
        return geometry.bounds
    elif isinstance(geometry, tuple([Dict, str] + [i for i in VALID_GEOJSON_GEOM_TYPES])):
        geojson = validate_geojson(geometry)
        if isinstance(geojson, VALID_GEOJSON_GEOM_TYPES):
            return geojson_to_shapely(geojson).bounds
        else:  # Feature or FeatureCollection; must extract geometry otherwise geojson_to_shapely() will throw ValueError
            return geojson_to_shapely(geojson[GEOJSON_GEOMETRY_KEYS[geojson["type"]]]).bounds
    else:
        raise TypeError("Cannot determine bounds from input geometry.")


def _earthsearch_version_from_stac_catalog_url(stac_catalog_url: str = EARTHSEARCH_URL):
    """Gets the EarthSearchCollections class for the given version of the STAC catalog URL."""
    stac_version = stac_catalog_url.split("/")[-1]
    if stac_version == "v0":
        from pixels_utils.stac_catalogs.earthsearch.v0 import EarthSearchCollections

        return EarthSearchCollections
    elif stac_version == "v1":
        from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections

        return EarthSearchCollections
    else:
        raise ValueError(f"STAC version '{stac_version}' not supported by pixels-utils.")


def _validate_collections(
    collection: Union[str, EarthSearchCollections], stac_catalog_url: str = EARTHSEARCH_URL
) -> str:
    """Validates that collection is a valid STAC collection for the given STAC catalog URL."""
    # TODO: Make more robust if needing to support more STAC catalogs
    earthsearch_collections = _earthsearch_version_from_stac_catalog_url(stac_catalog_url)

    collection = collection.name if isinstance(collection, earthsearch_collections) else collection
    assert collection in [
        c.name for c in earthsearch_collections
    ], f"Collection '{collection}' not supported by pixels-utils."
    return collection

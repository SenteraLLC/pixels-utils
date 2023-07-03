from typing import Any, Dict, Tuple, Union

from geo_utils.vector import validate_geojson
from geo_utils.vector._geojson import VALID_GEOJSON_GEOM_TYPES
from geo_utils.vector._shapely import VALID_SHAPELY_GEOM_TYPES
from geojson.feature import Feature

from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

Bounds = Tuple[float, float, float, float]


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


def _validate_geometry(geom: Any):
    """
    Validates the passed geometry object and raises an informative error if problem is detected.

    Args:
        geom (Any): Input geometry; should be GeoJSON object, shapely object, or WKT string.
    """
    if isinstance(geom, tuple([Dict, str])):  # geojson objects evaluate to True, so this catches all geojson objects
        geojson = validate_geojson(geom)
        if not isinstance(geojson, tuple(list(VALID_GEOJSON_GEOM_TYPES) + [Feature])):
            # FeatureCollection or GeometryCollection; geojson_to_shapely() will throw TypeError
            raise TypeError(
                f'Cannot determine bounds from geojson type of "{type(geojson).__name__}" because there are '
                "potentially multiple geometries present. Either choose a single geometry or merge the collection of "
                "geometries."
            )
    else:
        if not isinstance(geom, VALID_SHAPELY_GEOM_TYPES):
            # Not a dict, str, or shapely
            raise TypeError(
                f'Cannot determine bounds from input of "{type(geom).__name__}". Please pass a valid shapely or geojson object.'
            )

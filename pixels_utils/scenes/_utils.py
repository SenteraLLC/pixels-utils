from typing import Any, Dict, Tuple

from geo_utils.vector import geojson_to_shapely, validate_geojson
from geo_utils.vector._geojson import GEOJSON_GEOMETRY_KEYS, VALID_GEOJSON_GEOM_TYPES
from geo_utils.vector._shapely import VALID_SHAPELY_GEOM_TYPES

# from geo_utils.validate import ensure_valid_geometry


Bounds = Tuple[float, float, float, float]


def bounds_from_geojson_or_geometry(geometry: Any) -> Bounds:
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


# def bounds_from_geometry(geometry) -> Bounds:
#     geometry = ensure_valid_geometry(geometry, keys=["coordinates", "type"])
#     coords = geometry["coordinates"]
#     lngs = [lng for lng in _walk_geom_coords(coords, lambda c: c[0])]
#     lats = [lat for lat in _walk_geom_coords(coords, lambda c: c[1])]
#     return (min(lngs), min(lats), max(lngs), max(lats))


# def _walk_geom_coords(coordinates, get_fn) -> Iterator[float]:
#     for x in coordinates:
#         if isinstance(x, float):
#             yield get_fn(coordinates)
#         elif isinstance(x, dict):
#             yield from _walk_geom_coords(x["geometry"]["coordinates"], get_fn)
#         else:
#             yield from _walk_geom_coords(x, get_fn)

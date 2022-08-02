from typing import Any, Iterable, Union

from joblib import Memory  # type: ignore
from requests import Response, get, post

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import ENDPOINT_STATISTICS, PIXELS_URL
from pixels_utils.utilities import get_assets_expression_query, get_nodata

memory = Memory("/tmp/pixels-demo-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
def statistics(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
) -> Response:
    """Return asset's statistics for a GeoJSON.

    See: https://developmentseed.org/titiler/endpoints/stac/#statistics

    Args:
        scene_url: STAC item URL.
        assets: Asset names. If both <assets> and <expression> are set to None, will
        return all available assets. Default is None.
        expression: Rio-tiler's math expression with asset names (e.g.,
        "(B08-B04)/(B08+B04)"). Ignored when <assets> is set to a non-null value.
        Default is None.
        geojson: _description_. Defaults to None.
        mask_scl: _description_. Defaults to None.
        whitelist: _description_. Defaults to True.
        nodata: _description_. Defaults to None.
        gsd: _description_. Defaults to 20.
        resampling: _description_. Defaults to "nearest".
    """
    nodata = (
        get_nodata(scene_url, assets=assets, expression=expression)
        if nodata is None
        else nodata
    )

    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
    )

    if geojson is not None:
        return post(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            json=geojson,
        )
    else:
        return get(PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS), params=query)


# geojson_dict = {
#  'type': 'FeatureCollection',
#  'features': [{'id': '0',
#    'type': 'Feature',
#    'properties': {},
#    'geometry': {'type': 'MultiPolygon',
#     'coordinates': [(((-119.036182482726, 46.2399170074467),
#        (-119.044517426391, 46.2370808531824),
#        (-119.044048040987, 46.2391716403639),
#        (-119.041300124726, 46.2407629351223),
#        (-119.036182482726, 46.2399170074467)),)]},
#  }]
# }
# query_cmask= {
#     "url": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TGS_20220419_0_L2A",
#     "expression": "where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0.0));"  # Cloud-masked NDVI
# }
# query = {
#     'url': 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TGS_20220419_0_L2A',
#     'expression': 'where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0.0))'
# }
# r2 = post(
#     PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
#     params=query_cmask,
#     json=geojson_dict
# )


# NameToExpression = Dict[str, str]
# CLOUD_WEIGHT_KEY = "CLOUD_WEIGHT"
# Stats = OrderedDict[str, Dict[str, Any]]

# # TODO: These needs to be refactored pretty badly
# # TODO: Pretty sure it's possible to get multiple scenes for a day
# #       In which case, there needs to be some 'reduce' going on in here
# def getStats(
#     scene_items: List[Any],  # TODO: Type
#     geojson: Any,
#     name_to_expression: NameToExpression,
#     max_local_percent: int,
#     cogs_url: str,
#     pixels_url: str,
# ) -> Tuple[Stats, Dict[str, float]]:
#     def getStatName(expr: str) -> str:
#         return next((n for n, e in name_to_expression.items() if e == expr))

#     def getCloudWeightFirst(expr_and_stats):
#         return getStatName(expr_and_stats[0]) != CLOUD_WEIGHT_KEY

#     scene_stats: Stats = OrderedDict()
#     discarded: Dict[str, float] = {}
#     for s in scene_items:
#         scene_name = str(s)
#         scene_url = urllib.parse.urljoin(cogs_url, scene_name)

#         exprs = list(name_to_expression.values())
#         query_expression_list = ";".join(exprs)
#         params = {
#             "url": scene_url,
#             "expression": query_expression_list,
#         }

#         # TODO: Do something interesting with this
#         scene_cloud_cover_percent = s["eo:cloud_cover"]
#         pixels_stats_url = urllib.parse.urljoin(pixels_url, "./statistics")

#         # r = postToPixels(pixels_stats_url, params, geojson)
#         r = request_statistics(
#             scene_url,
#             assets=None,
#             expression=query_expression_list,
#             geojson=geojson,
#             mask_scl_valid=SCL_GROUP_ARABLE,
#             nodata=None,
#         )

#         # TODO: Make a proper sentinel value
#         try:
#             j = r.json()
#             raw_stats = j["features"][0]["properties"]["statistics"]
#         except (KeyError, IndexError) as e:
#             print("Malformed response for '{scene_name}'. Skipping")
#             discarded[scene_name] = -1

#         stats_it = iter(sorted(raw_stats.items(), key=getCloudWeightFirst))
#         _, cloud_weight_stats = next(stats_it)
#         cloud_cover_fraction = cloud_weight_stats["sum"] / cloud_weight_stats["count"]
#         cloud_cover_percent = cloud_cover_fraction * 100
#         if cloud_cover_percent <= max_local_percent:
#             scene_stats[scene_name] = OrderedDict()
#             for stat_expression, stats in stats_it:
#                 stat_name = getStatName(stat_expression)
#                 scene_stats[scene_name][stat_name] = stats
#         else:
#             date_block = scene_name.split("_", 2)[2].split("_")[0]
#             print(f"Local Cloud Cover for {date_block} exceeds threshold.")
#             print(f"  {int(cloud_cover_percent)} > {max_local_percent}")
#             discarded[scene_name] = cloud_cover_percent

#     return scene_stats, discarded

# @memory.cache
# def postToPixels(pixels_stats_url, params, geojson):
#     r = requests.post(
#         pixels_stats_url,
#         params=params,
#         json=geojson,
#     )
#     return r

# def getNameToExpression(cloud_weights: CloudWeights) -> NameToExpression:
#     scl_and_weight = (
#         (SCL.LOW_CLOUD, str(cloud_weights.low)),
#         (SCL.MEDIUM_CLOUD, str(cloud_weights.medium)),
#         (SCL.HIGH_CLOUD, str(cloud_weights.high)),
#     )
#     cloud_weight_expression = getCloudCoverExpression(iter(scl_and_weight))

#     name_to_unmasked_expression = {
#         "NDVI": "(B08-B04)/(B08+B04)",
#         "NDRE-705": "(B08-B05)/(B08+B05)",
#         "NDRE-740": "(B08-B06)/(B08+B06)",
#         "NDRE-783": "(B08-B07)/(B08+B07)",
#     }

#     name_to_expression = {
#         name: getCloudMaskedExpression(e)
#         for name, e in name_to_unmasked_expression.items()
#     }
#     name_to_expression[CLOUD_WEIGHT_KEY] = cloud_weight_expression
#     # TODO: Only enable for debugging
#     # name_to_expression['SCL'] = 'SCL'

#     return name_to_expression

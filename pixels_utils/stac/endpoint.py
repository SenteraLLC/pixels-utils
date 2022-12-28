import logging
from typing import Any, Dict, Iterable, List, Union

from geo_utils.validate import ensure_valid_feature, ensure_valid_featurecollection
from geo_utils.world import round_coordinate
from joblib import Memory  # type: ignore
from numpy.typing import ArrayLike
from requests import get, post

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.titiler import (
    ENDPOINT_CROP,
    ENDPOINT_INFO,
    ENDPOINT_STATISTICS,
    PIXELS_URL,
    QUERY_ASSETS,
    QUERY_URL,
    URL_PIXELS_CROP,
    URL_PIXELS_CROP_GEOJSON,
)
from pixels_utils.constants.types import STAC_crop, STAC_info, STAC_statistics
from pixels_utils.utilities import (  # find_geometry_from_geojson,
    get_assets_expression_query,
    get_nodata,
    to_pixel_dimensions,
)

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


def info_response(
    scene_url: str,
    assets: Iterable[str] = ("overview",),
) -> STAC_info:
    """
    _summary_

    Args:
        scene_url (str): _description_
        assets (Iterable[str], optional): _description_. Defaults to ("overview",).

    Returns:
        STAC_info: _description_
    """
    query = {
        QUERY_URL: scene_url,
        QUERY_ASSETS: assets,
    }
    return get(
        PIXELS_URL.format(endpoint=ENDPOINT_INFO),
        params=query,
    )


@memory.cache
def statistics_response(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    categorical: bool = False,
    c: List[Union[float, int]] = None,
    p: List[int] = None,
    histogram_bins: str = None,
    histogram_range: ArrayLike = None,
    clear_cache: bool = False,
) -> STAC_statistics:
    """Return asset's statistics for a GeoJSON.

    See: https://developmentseed.org/titiler/endpoints/stac/#statistics

    Args:
        scene_url (str): STAC item URL.
        assets (Iterable[str], optional): Asset names. If both `assets` and `expression` are set to `None`, will return
        all available assets. Default is None.

        expression (str, optional): Rio-tiler's math expression with asset names (e.g., "(B08-B04)/(B08+B04)"). Ignored
        when `assets` is set to a non-null value. Default is None.

        geojson (Any, optional): A valid GeoJSON-like `dict` Feature or FeatureCollection. Default is None.
        mask_scl (Iterable[SCL], optional): Sentinel-2 SCL classes to consider for pixel-based masking. If `None`,
        pixel-based masking is not implemented. The `whitelist` setting must be considered to determine if `mask_scl`
        classes are deemed to be valid or invalid. Default is None.

        whitelist (bool, optional): If `True`, the passed `mask_scl` classes are considerd "valid" for pixel-based
        masking; if `False`, the passed `mask_scl` classes are considered "invalid" for pixel-based masking. Default is
        True.

        nodata (Union[int, float], optional): Overwrites the NODATA value used by the source data. If `mask_scl` is set,
        "invalid" masked pixels are set to `nodata`. Default is None.

        gsd (Union[int, float], optional): Ground sampling distance. It is assumed (but not documented by TiTiler) that
        TiTiler will retrieve data at full data integrity/accuracy if `gsd` is matched to that of the inherent dataset
        being requested rather than using pyramiding/downsampling/tiling methods that TiTiler uses by default "behind
        the scenes". Default is 20.

        resampling (str, optional): Rasterio resampling method. See `rasterio.enums.Resampling.__members__` for a
        complete list of available resampling methods. Default is "nearest".

        categorical (bool, optional): Return statistics for categorical dataset. Default is False.
        c (List[Union[float, int]], optional): Pixels values for categories. Default is None.
        p (List[int], optional): Percentile values. Default is None.
        histogram_bins (str, optional): Histogram bins. Default is None.
        histogram_range (ArrayLike, optional): TODO: Asset/Expression specific min/max histogram bounds, e.g.:
        `((0,1000), (0,1000), (0,3000), (0,2000))` corresponding to
        `"histogram_range=0,1000, histogram_range=0,1000&histogram_range=0,3000&histogram_range=0,2000)"`. Default is
        None.

        clear_cache (bool, optional): Whether to clear the cache; useful if the request returns an error and you want to
        actually retry the request (rather than having the cached data returned). Default is False.
    """
    geojson_fc = None if geojson is None else ensure_valid_featurecollection(geojson, create_new=False)
    nodata = get_nodata(scene_url, assets=assets, expression=expression) if nodata is None else nodata

    query, _ = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson_fc,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
        categorical=categorical,
        c=c,
        p=p,
        histogram_bins=histogram_bins,
        histogram_range=histogram_range,
    )
    if clear_cache is True:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
    else:
        headers = {}

    if geojson_fc is not None:
        logging.debug(
            'POST request to "%s" with the following args:\nparams: %s\njson: %s\nheaders: %s',
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            query,
            geojson_fc,
            headers,
        )
        return post(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            json=geojson_fc,
            headers=headers,
        )
    else:
        logging.debug(
            'GET request to "%s" with the following args:\nparams: %s\nheaders: %s',
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            query,
            headers,
        )
        return get(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            headers=headers,
        )


@memory.cache
def crop_response(
    scene_url: str,
    assets: Iterable[str] = None,
    expression: str = None,
    geojson: Any = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    unscale: Union[bool, None] = None,
    clip: ArrayLike = None,
    rescale: ArrayLike = None,
    color_formula: Union[str, None] = None,
    colormap: Union[Dict, None] = None,
    colormap_name: Union[str, None] = None,
    return_mask: Union[bool, None] = None,
    format_stac: Union[str, None] = ".tif",
    clear_cache: bool = False,
) -> STAC_crop:
    """

    See: https://developmentseed.org/titiler/endpoints/stac/#crop-part

    Args:
        scene_url (str): STAC item URL.
        assets (Iterable[str], optional): Asset names. If both `assets` and `expression` are set to `None`, will return
        all available assets. Default is None.

        expression (str, optional): Rio-tiler's math expression with asset names (e.g., "(B08-B04)/(B08+B04)"). Ignored
        when `assets` is set to a non-null value. Default is None.

        geojson (Any, optional): A valid GeoJSON-like `dict` Feature or FeatureCollection. Default is None.
        mask_scl (Iterable[SCL], optional): Sentinel-2 SCL classes to consider for pixel-based masking. If `None`,
        pixel-based masking is not implemented. The `whitelist` setting must be considered to determine if `mask_scl`
        classes are deemed to be valid or invalid. Default is None.

        whitelist (bool, optional): If `True`, the passed `mask_scl` classes are considerd "valid" for pixel-based
        masking; if `False`, the passed `mask_scl` classes are considered "invalid" for pixel-based masking. Default is
        True.

        nodata (Union[int, float], optional): Overwrites the NODATA value used by the source data. If `mask_scl` is set,
        "invalid" masked pixels are set to `nodata`. Default is None.

        gsd (Union[int, float], optional): Ground sampling distance. It is assumed (but not documented by TiTiler) that
        TiTiler will retrieve data at full data integrity/accuracy if `gsd` is matched to that of the inherent dataset
        being requested rather than using pyramiding/downsampling/tiling methods that TiTiler uses by default "behind
        the scenes". Default is 20.

        resampling (str, optional): Rasterio resampling method. See `rasterio.enums.Resampling.__members__` for a
        complete list of available resampling methods. Default is "nearest".

        unscale (Union[bool, NoneType], optional): Apply dataset internal Scale/Offset. Default is None.
        clip (ArrayLike, optional): Min/Max data Rescaling. Comma (',') delimited Min,Max range. Can set multiple time
        for multiple bands. For example=["0,2000", "0,1000", "0,10000"] for bands 1, 2, 3, respectively. Note that to
        avoid confusion, this `clip` argument is an alias that points to the titiler `rescale` parameter. Default is
        None.

        rescale (ArrayLike, optional): See `clip`. Default is None.
        color_formula (Union[str, None], optional): Rio-color formula. CAUTION: USE ONLY FOR VISUALIZATION (i.e., will
        result in loss of data integrity). Default is None.

        colormap (Union[str, None], optional): JSON encoded custom Colormap. CAUTION: USE ONLY FOR VISUALIZATION (i.e.,
        will result in loss of data integrity). Default is None.

        colormap_name (Union[str, None], optional): Rio-tiler color map name. CAUTION: USE ONLY FOR VISUALIZATION (i.e.,
        will result in loss of data integrity). Default is None.

        return_mask (bool, optional): Add mask to the output data. Default is True.
        format_stac (str, optional): Output image format. If set to `None`, will be either JPEG or PNG depending how
        `return_mask` is set. Default is ".tif".

        clear_cache (bool, optional): Whether to clear the cache; useful if the request returns an error and you want to
        actually retry the request (rather than having the cached data returned). Default is False.
    """
    geojson_f = None if geojson is None else ensure_valid_feature(geojson, create_new=False)
    nodata = get_nodata(scene_url, assets=assets, expression=expression) if nodata is None else nodata
    if clip is None and rescale is not None:  # rescale is an alias for clip
        clip = rescale
        logging.warning(
            "Titiler `rescale` clips data to a lower and upper value (i.e., clamps data). It does not actually rescale "
            "the data. It's use may be misleading."
        )
    else:
        clip = None
    query, asset_main = get_assets_expression_query(
        scene_url,
        assets=assets,
        expression=expression,
        geojson=geojson_f,
        mask_scl=mask_scl,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
        unscale=unscale,
        rescale=clip,  # pass clip to rescale
        color_formula=color_formula,
        colormap=colormap,
        colormap_name=colormap_name,
        return_mask=return_mask,
    )
    if clear_cache is True:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
    else:
        headers = {}

    if geojson_f is not None:
        height, width = to_pixel_dimensions(geojson_f, gsd)
        r = post(
            URL_PIXELS_CROP_GEOJSON.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                width=width,
                height=height,
                format=format_stac,
            ),
            params=query,
            json=geojson_f,
            headers=headers,
        )
    else:
        info = info_response(scene_url, assets=(asset_main,)).json()[asset_main]
        minx, miny, maxx, maxy = info["bounds"]
        r = get(
            URL_PIXELS_CROP.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                minx=round_coordinate(minx, n_decimal_places=6)[0],
                miny=round_coordinate(miny, n_decimal_places=6)[0],
                maxx=round_coordinate(maxx, n_decimal_places=6)[0],
                maxy=round_coordinate(maxy, n_decimal_places=6)[0],
                width=info["width"],
                height=info["height"],
                format=format_stac,
            ),
            params=query,
            headers=headers,
        )
    return STAC_crop(r)

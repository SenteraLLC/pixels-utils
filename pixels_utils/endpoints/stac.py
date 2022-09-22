import logging
from datetime import date
from typing import Any, Dict, Iterable, List, Tuple, Union
from warnings import warn

import numpy.ma as ma
from geo_utils.general import round_dec_degrees
from geo_utils.validate_geojson import (
    ensure_valid_featurecollection,
    get_all_geojson_geometries,
)
from joblib import Memory  # type: ignore
from numpy import expand_dims as np_expand_dims
from numpy import logical_not as np_logical_not
from numpy import min_scalar_type as np_min_scalar_type
from numpy import ndarray as np_ndarray
from numpy.typing import ArrayLike
from pandas import DataFrame
from pandas import concat as pd_concat
from requests import get, post
from shapely.geometry import shape

from pixels_utils.constants.decorators import requires_rasterio
from pixels_utils.constants.sentinel2 import (
    ELEMENT84_L2A_SCENE_URL,
    SCL,
    SENTINEL_2_L2A_COLLECTION,
)
from pixels_utils.constants.titiler import (
    ENDPOINT_CROP,
    ENDPOINT_STATISTICS,
    PIXELS_URL,
    URL_PIXELS_CROP,
    URL_PIXELS_CROP_GEOJSON,
)
from pixels_utils.constants.types import STAC_crop, STAC_statistics
from pixels_utils.rasterio import ensure_data_profile_consistency
from pixels_utils.scenes import bbox_from_geometry, get_stac_scenes
from pixels_utils.utilities import (  # find_geometry_from_geojson,
    get_assets_expression_query,
    get_nodata,
    to_pixel_dimensions,
)

try:
    from rasterio import Env
    from rasterio.io import DatasetReader, MemoryFile
    from rasterio.profiles import Profile

    from pixels_utils.rasterio import combine_profile_tags, save_image
except ImportError:
    warn(
        "Optional dependency <rasterio> not imported. Some features are not available."
    )

memory = Memory("/tmp/pixels-demo-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


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
    histogram_bins: str = None,
) -> STAC_statistics:
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
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    nodata = (
        get_nodata(scene_url, assets=assets, expression=expression)
        if nodata is None
        else nodata
    )

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
        histogram_bins=histogram_bins,
    )

    if geojson_fc is not None:
        return post(
            PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS),
            params=query,
            json=geojson_fc,
        )
    else:
        return get(PIXELS_URL.format(endpoint=ENDPOINT_STATISTICS), params=query)


def scl_stats(
    scene_url: str,
    geojson: Any,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    **kwargs,
) -> tuple[Dict, Dict]:
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    r_scl = statistics_response(
        scene_url,
        assets="SCL",
        expression=None,
        geojson=geojson_fc,
        mask_scl=None,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
        categorical=True,
        c=list(range(12)),
    )
    # kwargs2 = {k:v for k,v in kwargs}
    stats_dict_scl, meta_dict_scl = _parse_stats_response(
        r_scl,
        **kwargs,
        # acquisition_time=scene["datetime"],
        # cloud_cover_scene_pct=scene["eo:cloud_cover"],
        scene_url=scene_url,
        assets="SCL",
        expression=None,
        geojson=geojson_fc,
        mask_scl=None,
        whitelist=whitelist,
        nodata=nodata,
        gsd=gsd,
        resampling=resampling,
        categorical=True,
        c=list(range(12)),
    )
    return stats_dict_scl, meta_dict_scl


@requires_rasterio
def statistics(
    date_start: Union[date, str],
    date_end: Union[date, str],
    geojson: Any = None,
    assets: Iterable[str] = None,
    expression: str = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    collection: str = SENTINEL_2_L2A_COLLECTION,
    categorical: bool = False,
    c: List[Union[float, int]] = None,
    histogram_bins: str = None,
) -> DataFrame:
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=True)
    df_scenes = get_stac_scenes(
        bbox_from_geometry(next(get_all_geojson_geometries(geojson_fc))),
        date_start,
        date_end,
    )
    # df_scenes = get_stac_scenes(bbox_from_geometry(geojson_fc), date_start, date_end)
    logging.info("Getting statistics for %s scenes", len(df_scenes))
    df_stats = None
    for _, scene in df_scenes.iterrows():
        # if i == 2:
        #     break
        scene_url = ELEMENT84_L2A_SCENE_URL.format(
            collection=collection, sceneid=scene["id"]
        )
        r = statistics_response(
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
            histogram_bins=histogram_bins,
        )
        stats_dict, meta_dict = _parse_stats_response(
            r,
            acquisition_time=scene["datetime"],
            cloud_cover_scene_pct=scene["eo:cloud_cover"],
            scene_url=scene_url,
            assets=assets,
            expression=expression,
            geojson=geojson_fc,
            mask_scl=mask_scl,
            whitelist=whitelist,
            nodata=nodata,
            gsd=gsd,
            resampling=resampling,
        )
        if "histogram" in stats_dict:
            del stats_dict["histogram"]
        stats_dict_scl, meta_dict_scl = scl_stats(
            scene_url,
            geojson_fc,
            whitelist,
            nodata,
            gsd,
            resampling,
            acquisition_time=scene["datetime"],
            cloud_cover_scene_pct=scene["eo:cloud_cover"],
        )
        scl_classes = [int(x) for x in stats_dict_scl["histogram"][1]]
        scl_counts = [int(x) for x in stats_dict_scl["histogram"][0]]
        scl_pcts = [
            (x / stats_dict_scl["count"]) * 100 for x in stats_dict_scl["histogram"][0]
        ]
        scl_hist_count = dict(zip(scl_classes, scl_counts))
        scl_hist_pct = dict(zip(scl_classes, scl_pcts))

        mask_scl_pixel_count = 0
        if whitelist is True:
            for scene_class in mask_scl:
                mask_scl_pixel_count += scl_hist_count[scene_class]
        elif whitelist is False:
            logging.info("WARNING!")
            pass  # TODO: Need to make this more robust
        stats_dict["whitelist_masked_pixels"] = mask_scl_pixel_count
        stats_dict["whitelist_masked_pct"] = (
            mask_scl_pixel_count / stats_dict_scl["count"]
        ) * 100

        meta_dict["scl_hist_count"] = scl_hist_count
        meta_dict["scl_hist_pct"] = scl_hist_pct

        df_stats_temp = _combine_stats_and_meta_dicts(stats_dict, meta_dict)
        df_stats = (
            df_stats_temp.copy()
            if df_stats is None
            else pd_concat([df_stats, df_stats_temp], axis=0)
        )
    return df_stats


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
    format_stac: str = ".tif",
) -> STAC_crop:
    """

    See: https://developmentseed.org/titiler/endpoints/stac/#crop-part

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
        format_stac: _description_. Defaults to ".tif".
    """
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    nodata = (
        get_nodata(scene_url, assets=assets, expression=expression)
        if nodata is None
        else nodata
    )
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
    )
    query = {k: v for k, v in query.items() if k not in ["height", "width"]}

    height, width = to_pixel_dimensions(geojson_fc, gsd)
    # minx, miny, maxx, maxy = shape(find_geometry_from_geojson(geojson)).bounds

    if geojson_fc is not None:
        r = post(
            URL_PIXELS_CROP_GEOJSON.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                width=width,
                height=height,
                format=format_stac,
            ),
            params=query,
            json=geojson_fc,
        )
    else:
        minx, miny, maxx, maxy = shape(geojson_fc).bounds
        r = get(
            URL_PIXELS_CROP.format(
                pixels_endpoint=PIXELS_URL.format(endpoint=ENDPOINT_CROP),
                minx=round_dec_degrees(minx, n_decimal_places=6),
                miny=round_dec_degrees(miny, n_decimal_places=6),
                maxx=round_dec_degrees(maxx, n_decimal_places=6),
                maxy=round_dec_degrees(maxy, n_decimal_places=6),
                width=width,
                height=height,
                format=format_stac,
            ),
            params=query,
        )
    return STAC_crop(r)


def _combine_stats_and_meta_dicts(stats_dict: Dict, meta_dict: Dict) -> DataFrame:
    master_dict = {}
    master_dict["scene_url"] = meta_dict.pop("scene_url")
    master_dict["acquisition_time"] = meta_dict.pop("acquisition_time")
    master_dict["cloud_cover_scene_pct"] = meta_dict.pop("cloud_cover_scene_pct")
    master_dict.update(stats_dict)
    master_dict["metadata"] = meta_dict
    # df_stats = DataFrame.from_records(
    #     data=[master_dict],
    #     # index=pd.Index(data=[scene_url], name="scene_url")
    # )
    return DataFrame.from_records(data=[master_dict])


def _parse_stats_response(r: STAC_statistics, **kwargs) -> tuple[Dict, Dict]:
    data_dict = r.json()
    stats_key = list(data_dict["features"][0]["properties"]["statistics"].keys())[0]
    stats_dict = data_dict["features"][0]["properties"]["statistics"][stats_key].copy()
    meta_dict = {k: v for k, v in kwargs.items()}
    return stats_dict, meta_dict


@requires_rasterio
def _response_to_rasterio(r: STAC_crop) -> DatasetReader:
    """Parses STAC_crop response into rasterio dataset.

    Args:
        r (STAC_crop): _description_

    Example:
        >>> with Env(), _response_to_rasterio(r.content) as ds:
        >>>     data = ds.read()
        >>>     profile = ds.profile
        >>>     tags = ds.tags()

    Returns:
        DatasetReader: _description_
    """
    with MemoryFile(r.content) as m:
        ds = m.open()
    return ds


@requires_rasterio
def crop(r: STAC_crop) -> Tuple[np_ndarray, Profile]:
    """
    Eqivalent to:
        >>> r = crop_response(...)
        >>> ds = _response_to_rasterio(...)
        >>> ds.data, ds.profile
    """
    with Env(), _response_to_rasterio(r) as ds:
        # data = ds.read()
        data = ds.read(masked=False)
        profile = combine_profile_tags(ds)

    # data_out, profile_out = geoml_metadata(data, profile)
    return data, profile


def mask_stac_crop(
    data: ArrayLike, profile: Profile, nodata: Union[float, int] = 0
) -> tuple[np_ndarray, Profile]:
    """Sets the last band of <data> as a mask layer, setting nodata.

    Note:
        The pixels.sentera.com/stac/crop/abc...xyz.tif endpoint returns a 3D array, with
        the 3rd dimension being a binary (0 or 255) mask band. This function does two
        things:

            Adjusts data so the 1st dimension (number of bands) has a similar length to
            the number of bands.

            Applies the pixels.sentera.com mask band to a numpy.mask

    Note:
        rasterio.DataSetReader.read() returns array with shape (bands, rows, columns)

    mask2 = None
    # Could we always request the SCL layer with request_crop so we know
    # what is outside geojson and what is actually masked? Problem is that they both
    # show up as "nodata".
    # Better to probably get SCL specifically if/when it is needed.

    """
    nodata = 0 if nodata is None else nodata

    mask = np_expand_dims(data[-1, :, :], axis=0)  # stac/crop mask
    data_no_alpha = data[:-1, :, :]  # get all but last band
    # data_no_alpha[np_repeat(mask, data_no_alpha.shape[0], axis=0) == 0.0] = ma.masked
    array_mask = ma.masked_array(data_no_alpha, mask=np_logical_not(mask))

    if (
        not ma.maximum_fill_value(array_mask)
        <= nodata
        <= ma.minimum_fill_value(array_mask)
    ):
        array_mask = array_mask.astype(
            np_min_scalar_type(nodata)
        )  # set array dtype so nodata is valid
    ma.set_fill_value(array_mask, nodata)
    profile.update(nodata=nodata)

    array_mask, profile = ensure_data_profile_consistency(
        array_mask, profile, driver=profile["driver"]
    )
    return array_mask, profile


def write_to_file(path: str, data: ArrayLike, profile: Profile):
    """
    path = "/mnt/c/Users/Tyler/Downloads/test2.tif"
    """
    # data_out = data[0]
    save_image(data, profile, path, driver="Gtiff", keep_xml=False)

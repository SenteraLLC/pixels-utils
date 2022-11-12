import logging
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Tuple, Union

import pytz
from geo_utils.validate import ensure_valid_featurecollection, get_all_geojson_geometries
from numpy import ndarray as np_ndarray
from pandas import DataFrame
from pandas import concat as pd_concat
from retry import retry

from pixels_utils.constants.decorators import requires_rasterio
from pixels_utils.constants.sentinel2 import ELEMENT84_L2A_SCENE_URL, SCL, SENTINEL_2_L2A_COLLECTION
from pixels_utils.constants.types import STAC_crop
from pixels_utils.scenes import bbox_from_geometry, get_stac_scenes
from pixels_utils.stac.endpoint import statistics_response
from pixels_utils.utils_crop import response_to_rasterio
from pixels_utils.utils_statistics import (
    combine_stats_and_meta_dicts,
    compute_whitelist_stats,
    parse_stats_response,
    parse_stats_response_blank,
)

try:
    from rasterio import Env
    from rasterio.profiles import Profile

    from pixels_utils.rasterio import combine_profile_tags
except ImportError:
    logging.exception("Optional dependency <rasterio> not imported. Some features are not available.")


@retry(KeyError, tries=3, delay=2)
def scl_stats(
    scene_url: str,
    geojson: Any,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    acquisition_time: str = None,
    cloud_cover_scene_pct: float = None,
    clear_cache_iter=iter([False, True, True]),
) -> tuple[Dict, Dict]:
    geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
    stats_kwargs = {
        "scene_url": scene_url,
        "assets": "SCL",
        "expression": None,
        "geojson": geojson_fc,
        "mask_scl": None,
        "whitelist": whitelist,
        "nodata": nodata,
        "gsd": gsd,
        "resampling": resampling,
        "categorical": True,
        "c": list(range(12)),
        "histogram_bins": None,
    }

    scene_dict = {
        "request_time_scl": (datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S%z")),
        "acquisition_time": acquisition_time,
        "cloud_cover_scene_pct": cloud_cover_scene_pct,
    }
    r_scl = statistics_response(**stats_kwargs, clear_cache=next(clear_cache_iter))
    stats_dict_scl, meta_dict_scl = parse_stats_response(r_scl, **scene_dict, **stats_kwargs)
    return stats_dict_scl, meta_dict_scl


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
    # in this case, <next> returns only the first geometry.
    # TODO: Should there be a warning or exception raised if there happen to be multiple geometries passed?
    df_scenes = get_stac_scenes(
        bbox_from_geometry(next(get_all_geojson_geometries(geojson_fc))),
        date_start,
        date_end,
    )
    # df_scenes = get_stac_scenes(bbox_from_geometry(geojson_fc), date_start, date_end)
    if len(df_scenes) > 0:
        logging.info("Getting STAC statistics. Number of scenes: %s", len(df_scenes))
    else:
        logging.warning("No valid scenes for AOI from %s to %s.", date_start, date_end)
        return

    stats_kwargs = {
        "scene_url": None,
        "assets": assets,
        "expression": expression,
        "geojson": geojson_fc,
        # "geojson": geojson_fc.wkt,
        "mask_scl": mask_scl,
        "whitelist": whitelist,
        "nodata": nodata,
        "gsd": gsd,
        "resampling": resampling,
        "categorical": categorical,
        "c": c,
        "histogram_bins": histogram_bins,
    }
    df_stats = None
    for i, scene in df_scenes.iterrows():
        # if i == 2:
        #     break
        stats_kwargs["scene_url"] = ELEMENT84_L2A_SCENE_URL.format(collection=collection, sceneid=scene["id"])
        acquisition_time = scene["datetime"]
        cloud_cover_scene_pct = scene["eo:cloud_cover"]

        @retry(KeyError, tries=3, delay=2)
        def run_stats(
            acquisition_time: str = None,
            cloud_cover_scene_pct: float = None,
            clear_cache_iter=iter([False, True, True]),
        ):
            """
            Runs statististics_response() and parse_stats_response() together so if
            KeyError it can retry.
            """
            scene_dict = {
                "request_time": (datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S%z")),
                "acquisition_time": acquisition_time,
                "cloud_cover_scene_pct": cloud_cover_scene_pct,
            }
            r = statistics_response(
                **stats_kwargs,
                clear_cache=next(clear_cache_iter),  # Clears cache after 1st try in case error is raised
            )

            (stats_dict, meta_dict,) = parse_stats_response(  # Must be in same function as statistics_response() call
                r, **scene_dict, **stats_kwargs
            )
            return stats_dict, meta_dict

        # TODO: A separate nested function that only runs if r has an error

        try:
            stats_dict, meta_dict = run_stats(
                acquisition_time,
                cloud_cover_scene_pct,
                clear_cache_iter=iter([False, True, True]),
            )
            stats_dict_scl, meta_dict_scl = scl_stats(
                stats_kwargs["scene_url"],
                geojson_fc,
                whitelist,
                nodata,
                gsd,
                resampling,
                acquisition_time=acquisition_time,
                cloud_cover_scene_pct=cloud_cover_scene_pct,
                clear_cache_iter=iter([False, True, True]),
            )
            (
                whitelist_pixels,
                whitelist_pct,
                scl_hist_count,
                scl_hist_pct,
            ) = compute_whitelist_stats(stats_dict_scl, whitelist, mask_scl)
            stats_dict["whitelist_pixels"] = whitelist_pixels
            stats_dict["whitelist_pct"] = whitelist_pct
            meta_dict["scl_hist_count"] = scl_hist_count
            meta_dict["scl_hist_pct"] = scl_hist_pct
            meta_dict["request_time_scl"] = meta_dict_scl["request_time_scl"]
            if "histogram" in stats_dict:
                del stats_dict["histogram"]
            logging.info("Retrieving scene %s/%s: SUCCESS", i + 1, len(df_scenes))
        except TypeError:  # Fill in what we can so program can continue for other scenes in date range.
            scene_dict = {
                "request_time": None,
                "acquisition_time": acquisition_time,
                "cloud_cover_scene_pct": cloud_cover_scene_pct,
            }
            stats_dict, meta_dict = parse_stats_response_blank(
                **scene_dict,
                **stats_kwargs,
                scl_hist_count=None,
                scl_hist_pct=None,
                request_time_scl=None,
            )
            logging.warning("Retrieving scene  %s/%s: TypeError", i + 1, len(df_scenes))
        except KeyError:
            scene_dict = {
                "request_time": None,
                "acquisition_time": acquisition_time,
                "cloud_cover_scene_pct": cloud_cover_scene_pct,
            }
            stats_dict, meta_dict = parse_stats_response_blank(
                **scene_dict,
                **stats_kwargs,
                scl_hist_count=None,
                scl_hist_pct=None,
                request_time_scl=None,
            )
            logging.warning("Retrieving scene %s/%s: KeyError", i + 1, len(df_scenes))

        logging.debug("Scene URL: %s", stats_kwargs["scene_url"])
        df_stats_temp = combine_stats_and_meta_dicts(stats_dict, meta_dict)
        df_stats = df_stats_temp.copy() if df_stats is None else pd_concat([df_stats, df_stats_temp], axis=0)
    return df_stats


@requires_rasterio
def crop(r: STAC_crop) -> Tuple[np_ndarray, Profile]:
    """
    Eqivalent to:
        >>> r = crop_response(...)
        >>> ds = response_to_rasterio(...)
        >>> ds.data, ds.profile
    """
    with Env(), response_to_rasterio(r) as ds:
        # data = ds.read()
        data = ds.read(masked=False)
        profile = combine_profile_tags(ds)

    # data_out, profile_out = geoml_metadata(data, profile)
    return data, profile

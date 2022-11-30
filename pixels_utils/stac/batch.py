import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union

import pytz
from geo_utils.validate import ensure_valid_feature, ensure_valid_featurecollection, get_all_geojson_geometries
from numpy import ndarray as np_ndarray
from numpy.typing import ArrayLike
from pandas import DataFrame
from pandas import concat as pd_concat
from pyproj import CRS
from retry import retry

from pixels_utils import __version__ as PIXELS_UTILS_VERSION  # noqa
from pixels_utils.constants.decorators import requires_rasterio
from pixels_utils.constants.sentinel2 import ELEMENT84_L2A_SCENE_URL, SCL, SENTINEL_2_L2A_COLLECTION
from pixels_utils.scenes import bbox_from_geometry, get_stac_scenes
from pixels_utils.stac.endpoint import crop_response, statistics_response
from pixels_utils.utils_crop import count_geojson_pixels, count_valid_whitelist_pixels
from pixels_utils.utils_statistics import (
    combine_stats_and_meta_dicts,
    compute_whitelist_stats,
    parse_stats_response,
    parse_stats_response_blank,
)

try:
    from geo_utils.raster import save_rasterio
    from rasterio.profiles import Profile

    from pixels_utils.utils_crop import parse_crop_response
except ImportError:
    logging.exception("Optional dependency <rasterio> not imported. Some features are not available.")


# @retry(KeyError, tries=3, delay=2)
# def scl_stats(
#     scene_url: str,
#     geojson: Any,
#     whitelist: bool = True,
#     nodata: Union[int, float] = None,
#     gsd: Union[int, float] = 20,
#     resampling: str = "nearest",
#     acquisition_time: str = None,
#     cloud_cover_scene_pct: float = None,
#     clear_cache_iter=iter([False, True, True]),
# ) -> tuple[Dict, Dict]:
#     geojson_fc = ensure_valid_featurecollection(geojson, create_new=False)
#     stats_kwargs = {
#         "scene_url": scene_url,
#         "assets": "SCL",
#         "expression": None,
#         "geojson": geojson_fc,
#         "mask_scl": None,
#         "whitelist": whitelist,
#         "nodata": nodata,
#         "gsd": gsd,
#         "resampling": resampling,
#         "categorical": True,
#         "c": list(range(12)),
#         "histogram_bins": None,
#     }

#     scene_dict = {
#         "request_time_scl": (datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S%z")),
#         "acquisition_time": acquisition_time,
#         "cloud_cover_scene_pct": cloud_cover_scene_pct,
#     }
#     r_scl = statistics_response(**stats_kwargs, clear_cache=next(clear_cache_iter))
#     stats_dict_scl, meta_dict_scl = parse_stats_response(r_scl, **scene_dict, **stats_kwargs)
#     return stats_dict_scl, meta_dict_scl


def statistics(
    date_start: Union[date, str],
    date_end: Union[date, str],
    geojson: Any = None,
    collection: str = SENTINEL_2_L2A_COLLECTION,
    assets: Iterable[str] = None,
    expression: str = None,
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
) -> DataFrame:
    geojson_fc = None if geojson is None else ensure_valid_featurecollection(geojson, create_new=True)
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
        "mask_scl": mask_scl,
        "whitelist": whitelist,
        "nodata": nodata,
        "gsd": gsd,
        "resampling": resampling,
        "categorical": categorical,
        "c": c,
        "p": p,
        "histogram_bins": histogram_bins,
        "histogram_range": histogram_range,
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
            stats_kwargs: Dict = None,
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

            stats_kwargs = {k: v for k, v in stats_kwargs.items()}
            stats_kwargs["version"] = PIXELS_UTILS_VERSION
            (stats_dict, meta_dict,) = parse_stats_response(  # Must be in same function as statistics_response() call
                r, **scene_dict, **stats_kwargs
            )
            return stats_dict, meta_dict

        # TODO: A separate nested function that only runs if r has an error

        try:
            stats_dict, meta_dict = run_stats(
                acquisition_time,
                stats_kwargs,
                cloud_cover_scene_pct,
                clear_cache_iter=iter([False, True, True]),
            )

            stats_kwargs_scl = {
                k: v for k, v in stats_kwargs.items() if k not in ["assets", "expression", "mask_scl", "whitelist"]
            }
            stats_kwargs_scl["expression"] = "SCL"
            stats_dict_scl, meta_dict_scl = run_stats(
                acquisition_time,
                stats_kwargs,
                cloud_cover_scene_pct,
                clear_cache_iter=iter([False, True, True]),
            )

            # stats_dict_scl, meta_dict_scl = scl_stats(
            #     stats_kwargs["scene_url"],
            #     geojson_fc,
            #     whitelist,
            #     nodata,
            #     gsd,
            #     resampling,
            #     acquisition_time=acquisition_time,
            #     cloud_cover_scene_pct=cloud_cover_scene_pct,
            #     clear_cache_iter=iter([False, True, True]),
            # )
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
def crop(
    date_start: Union[date, str],
    date_end: Union[date, str],
    geojson: Any = None,
    collection: str = SENTINEL_2_L2A_COLLECTION,
    assets: Iterable[str] = None,
    expression: str = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    nodata: Union[int, float] = None,
    gsd: Union[int, float] = 20,
    resampling: str = "nearest",
    unscale: Union[bool, None] = None,
    rescale: ArrayLike = None,
    color_formula: Union[str, None] = None,
    colormap: Union[Dict, None] = None,
    colormap_name: Union[str, None] = None,
    return_mask: Union[bool, None] = None,
    format_stac: Union[str, None] = ".tif",
    crs: CRS = CRS.from_epsg(4326),
    dir_out: Path = None,
    minimum_whitelist: Union[int, float] = None,
    max_images: Union[int, float] = None,
) -> Tuple[np_ndarray, Profile]:
    geojson_f = None if geojson is None else ensure_valid_feature(geojson, create_new=False)
    # in this case, <next> returns only the first geometry.
    # TODO: Should there be a warning or exception raised if there happen to be multiple geometries passed?
    df_scenes = get_stac_scenes(
        bbox_from_geometry(next(get_all_geojson_geometries(geojson_f))),
        date_start,
        date_end,
    )
    # df_scenes = get_stac_scenes(bbox_from_geometry(geojson_fc), date_start, date_end)
    if len(df_scenes) > 0:
        logging.info("Getting STAC crop rasters. Number of scenes: %s", len(df_scenes))
    else:
        logging.warning("No valid scenes for AOI from %s to %s.", date_start, date_end)
        return

    crop_kwargs = {
        "scene_url": None,
        "assets": assets,
        "expression": expression,
        "geojson": geojson_f,
        "mask_scl": mask_scl,
        "whitelist": whitelist,
        "nodata": nodata,
        "gsd": gsd,
        "resampling": resampling,
        "unscale": unscale,
        "rescale": rescale,
        "color_formula": color_formula,
        "colormap": colormap,
        "colormap_name": colormap_name,
        "return_mask": return_mask,
        "format_stac": format_stac,
    }

    img_count = 0
    for i, scene in df_scenes.iterrows():
        # if i > -1:
        #     break
        crop_kwargs["scene_url"] = ELEMENT84_L2A_SCENE_URL.format(collection=collection, sceneid=scene["id"])
        acquisition_time = scene["datetime"]
        cloud_cover_scene_pct = scene["eo:cloud_cover"]

        @retry(KeyError, tries=3, delay=2)
        def run_crop(
            acquisition_time: str = None,
            crop_kwargs: Dict = None,
            cloud_cover_scene_pct: float = None,
            clear_cache_iter=iter([False, True, True]),
        ):
            """Runs crop_response() and count_geojson_pixels() together so if KeyError it can retry."""
            scene_tags = {
                "request_time": (datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S%z")),
                "acquisition_time": acquisition_time,
                "cloud_cover_scene_pct": cloud_cover_scene_pct,
            }
            r = crop_response(
                **crop_kwargs,
                clear_cache=next(clear_cache_iter),  # Clears cache after 1st try in case error is raised
            )

            pixels_params = {k: v for k, v in crop_kwargs.items()}
            if "mask_scl" in pixels_params:
                pixels_params["mask_scl"] = [i.name for i in pixels_params["mask_scl"]]
            pixels_params["version"] = PIXELS_UTILS_VERSION
            data, profile, tags = parse_crop_response(  # Must be in same function as crop_response() call
                r, **scene_tags, pixels_params=pixels_params
            )
            # Update profile with stats
            band_names = (
                (pixels_params["expression"],)
                if isinstance(pixels_params["expression"], str)
                else pixels_params["expression"]
            )
            tags["geojson_stats"] = count_geojson_pixels(data, band_names)
            return data, profile, tags

        # TODO: A separate nested function that only runs if r has an error
        try:
            data, profile, tags = run_crop(
                acquisition_time,
                crop_kwargs,
                cloud_cover_scene_pct,
                clear_cache_iter=iter([True, True, True]),
            )
            if crop_kwargs["mask_scl"]:  # only get SCL if first request had masking by SCL performed
                crop_kwargs_scl = {
                    k: v for k, v in crop_kwargs.items() if k not in ["assets", "expression", "mask_scl", "whitelist"]
                }
                crop_kwargs_scl["expression"] = "SCL"
                # crop_kwargs_scl["nodata"] = -1
                data_scl, profile_scl, tags_scl = run_crop(
                    acquisition_time,
                    crop_kwargs_scl,
                    cloud_cover_scene_pct,
                    clear_cache_iter=iter([True, True, True]),
                )
                tags["mask_scl_stats"] = count_valid_whitelist_pixels(data_scl, mask_scl, whitelist)
                tags["request_time_scl"] = tags_scl["request_time"]
            else:
                tags["mask_scl_stats"] = None
                tags["request_time_scl"] = None
            logging.info("Retrieving scene %s/%s: SUCCESS", i + 1, len(df_scenes))
        except TypeError:  # Fill in what we can so program can continue for other scenes in date range.
            data, profile, tags = None, None, None
            logging.warning("Retrieving scene  %s/%s: TypeError", i + 1, len(df_scenes))
        except KeyError:
            data, profile, tags = None, None, None
            logging.warning("Retrieving scene %s/%s: KeyError", i + 1, len(df_scenes))

        logging.debug("Scene URL: %s", crop_kwargs["scene_url"])
        if data is None or profile is None:
            continue
        if tags["mask_scl_stats"]["whitelist_pct"] >= minimum_whitelist:
            # data_out, profile_out = geoml_metadata(data, profile)
            # geojson_hash = int(hashlib.sha256(dumps(geojson).encode("utf-8")).hexdigest(), 16) % 10**6
            # fname_out = "_".join([scene["id"], "sha256-" + str(geojson_hash)]) + format_stac
            fname_out = "_".join([scene["id"], f"{dir_out.parts[-1]}"]) + format_stac
            band_names = (
                (crop_kwargs["expression"],)
                if isinstance(crop_kwargs["expression"], str)
                else crop_kwargs["expression"]
            )

            save_rasterio(
                dir_out=dir_out,
                fname_out=fname_out,
                arr=data,
                profile=profile,
                tags=tags,
                band_description=band_names,
                crs=crs,
            )
            img_count += 1
        if img_count >= max_images:
            logging.info("Maximum allowable image count (%s) is met. Stopping.", max_images)
            break

    # with WarpedVRT(ds, crs=crs) as vrt:
    #     ds_warp
    # with rasterio.open('tests/data/RGB.byte.tif') as src:
    # with WarpedVRT(src, crs=crs) as vrt:
    #     data = vrt.read()
    #     # TODO: Either return vrt (?) or save vrt.data/vrt.profile to disk

    # # data_out, profile_out = geoml_metadata(data, profile)
    # return data, profile

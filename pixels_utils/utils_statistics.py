from json import dumps as json_dumps
from typing import Dict

from pandas import DataFrame

from pixels_utils.constants.types import STAC_statistics


def combine_stats_and_meta_dicts(stats_dict: Dict, meta_dict: Dict) -> DataFrame:
    master_dict = {}
    master_dict["scene_url"] = meta_dict.pop("scene_url")
    master_dict["acquisition_time"] = meta_dict.pop("acquisition_time")
    master_dict["cloud_cover_scene_pct"] = meta_dict.pop("cloud_cover_scene_pct")
    master_dict.update(stats_dict)
    master_dict["metadata"] = json_dumps(meta_dict)
    # df_stats = DataFrame.from_records(
    #     data=[master_dict],
    #     # index=pd.Index(data=[scene_url], name="scene_url")
    # )
    return DataFrame.from_records(data=[master_dict])


def compute_whitelist_stats(stats_dict_scl, whitelist, mask_scl):
    scl_classes = [int(x) for x in stats_dict_scl["histogram"][1]]
    scl_counts = [int(x) for x in stats_dict_scl["histogram"][0]]
    scl_pcts = [
        (x / stats_dict_scl["count"]) * 100 for x in stats_dict_scl["histogram"][0]
    ]
    scl_hist_count = dict(zip(scl_classes, scl_counts))
    scl_hist_pct = dict(zip(scl_classes, scl_pcts))
    if whitelist is True:
        whitelist_pixels = sum(
            [scl_hist_count[scene_class] for scene_class in mask_scl]
        )
    else:
        whitelist_pixels = stats_dict_scl["count"] - sum(
            [scl_hist_count[scene_class] for scene_class in mask_scl]
        )
    whitelist_pct = (whitelist_pixels / stats_dict_scl["count"]) * 100
    return whitelist_pixels, whitelist_pct, scl_hist_count, scl_hist_pct


def parse_stats_response(r: STAC_statistics, **kwargs) -> tuple[Dict, Dict]:
    data_dict = r.json()
    stats_key = list(data_dict["features"][0]["properties"]["statistics"].keys())[0]
    stats_dict = data_dict["features"][0]["properties"]["statistics"][stats_key].copy()
    meta_dict = {k: v for k, v in kwargs.items()}
    return stats_dict, meta_dict


def parse_stats_response_blank(**kwargs) -> tuple[Dict, Dict]:
    stats_keys = [
        "min",
        "max",
        "mean",
        "count",
        "sum",
        "std",
        "median",
        "majority",
        "minority",
        "unique",
        # "histogram",
        "valid_percent",
        "masked_pixels",
        "valid_pixels",
        "percentile_98",
        "percentile_2",
        "whitelist_pixels",
        "whitelist_pct",
    ]
    stats_dict = {k: None for k in stats_keys}
    meta_dict = {k: v for k, v in kwargs.items()}
    return stats_dict, meta_dict

import logging
from datetime import datetime
from typing import Union

from geojson.feature import Feature
from numpy import float32
from pandas import DataFrame, Series, concat
from rasterio import MemoryFile
from rasterio.enums import Resampling
from rasterio.sample import sample_gen
from tqdm import tqdm

from pixels_utils.scenes import parse_nested_stac_data
from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_SCENE_URL, EarthSearchCollections, Expression
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Crop, QueryParamsCrop, QueryParamsStatistics, Statistics
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group


def filter_scenes_with_all_nodata(
    df_scenes: DataFrame,
    feature: Feature,
    expression_obj: Expression,
    gsd: Union[float, int] = 10,
    nodata: Union[float, int] = -999,
) -> list:
    """
    Finds the index of all scenes without any valid pixels across the extent of the field group geometry.

    Note:
        The Titiler/sentera.pixels endpoint has a nuance that if all pixels within a spatial query are NODATA, then
        the Statistics endpoint returns statistics values equivalent to the NODATA value set. This function finds
        the index of all scenes where this is the case so they can be removed from the list of scenes to process.

    Args:
        df_scenes (DataFrame): Initial list of scenes to process.

    Returns:
        list: Index values of df_scenes that can safely be removed because they do not have any valid pixels.
    """
    df_scene_properties = parse_nested_stac_data(df=df_scenes, column="properties")

    ind_nodata = []
    for ind in tqdm(
        list(df_scenes.index),
        desc="Filtering out scenes where clouds are covering the plot area",
    ):
        scene = df_scenes.loc[ind]
        properties = df_scene_properties.loc[ind]
        date = datetime.strptime(properties["datetime"].split("T")[0], "%Y-%m-%d")
        # if date > datetime(2023, 5, 30):
        #     break

        scene_url = EARTHSEARCH_SCENE_URL.format(collection=EarthSearchCollections.sentinel_2_l2a.name, id=scene["id"])

        query_params = QueryParamsStatistics(
            url=scene_url,
            feature=feature,
            expression=expression_obj.expression,
            asset_as_band=True,
            coord_crs=None,
            gsd=gsd,
            nodata=nodata,
            resampling=Resampling.nearest.name,
        )

        stats_arable_wlist = Statistics(
            query_params=query_params,
            clear_cache=False,
            titiler_endpoint=TITILER_ENDPOINT,
            mask_enum=Sentinel2_SCL_Group.ARABLE,
            mask_asset="scl",
            whitelist=True,
        )

        expression_ = list(stats_arable_wlist.response.json()["properties"]["statistics"].keys())[0]
        stats = stats_arable_wlist.response.json()["properties"]["statistics"][expression_]
        # if stats["mean"] == nodata:
        if stats["min"] == nodata:
            # Indicates at least one pixel from statistics query is set to NODATA (i.e., masked)
            logging.debug(
                "%s: No valid pixels available",
                date.date(),
            )
            ind_nodata += [ind]

        else:
            logging.debug(
                "%s: %s valid pixels (Mean NDVI = %s)",
                date.date(),
                stats["count"],
                round(stats["mean"], 2),
            )
    return ind_nodata


def get_satellite_expression_as_df(
    gdf_fields_subset: DataFrame,
    scene: Series,
    feature: Feature,
    expression_obj: Expression,
    gsd: Union[float, int],
    nodata: Union[float, int],
) -> DataFrame:
    """
    Retrieves image for `scene_url` via sentera.pixels.com based on `expression_obj`, then samples the NDVI value for
    each centroid in `gdf_fields_subset`.


    Returns:
        DataFrame: NDVI values with "field_id" and "geom_id" join keys.
    """
    query_params_crop_ndvi = QueryParamsCrop(
        url=EARTHSEARCH_SCENE_URL.format(collection=EarthSearchCollections.sentinel_2_l2a.name, id=scene["id"]),
        feature=feature,
        gsd=gsd,
        format_=".tif",
        expression=expression_obj.expression,
        asset_as_band=True,
        nodata=nodata,
        resampling=Resampling.nearest.name,
    )
    crop_arable_wlist = Crop(
        query_params=query_params_crop_ndvi,
        clear_cache=False,
        titiler_endpoint=TITILER_ENDPOINT,
        mask_enum=Sentinel2_SCL_Group.ARABLE,
        mask_asset="scl",
        whitelist=True,
    )
    data_mask, profile_mask, tags = crop_arable_wlist.to_rasterio(
        **{
            "dtype": float32,
            "band_names": [expression_obj.short_name],
            "band_description": [expression_obj.short_name],
        }
    )

    with MemoryFile() as memfile:
        with memfile.open(**profile_mask) as src:  # Open as DatasetWriter
            src.write(data_mask)

            # Do not sort xy in sample_gen function; order must be maintained for merging to primary keys
            df_data = DataFrame(
                data=sample_gen(
                    src,
                    xy=list(gdf_fields_subset["geom"].apply(lambda geometry: geometry.centroid.coords[0])),
                ),
                # columns=["ndvi"],
                columns=[expression_obj.short_name],
            )
    # Remove any rows where ndvi is set to NODATA
    # df_data.drop(df_data.loc[df_data["ndvi"] == nodata].index, inplace=True)
    df_data.drop(df_data.loc[df_data[expression_obj.short_name] == nodata].index, inplace=True)
    df_data.insert(0, "scene_id", scene["id"])
    df_data.insert(1, "datetime", scene["datetime"])
    df_data = concat(
        [
            gdf_fields_subset[["site_name", "plot_id", "field_id", "geom_id"]].reset_index(drop=True),
            df_data,
        ],
        axis=1,
    )
    return df_data

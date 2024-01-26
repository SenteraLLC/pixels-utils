from typing import Union

from geojson.feature import Feature
from numpy import float32
from pandas import DataFrame, Series, concat
from rasterio import MemoryFile
from rasterio.enums import Resampling
from rasterio.sample import sample_gen

from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_SCENE_URL, EarthSearchCollections, Expression
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac.crop._crop import Crop, QueryParamsCrop
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group


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

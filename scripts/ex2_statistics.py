import logging
from pprint import pprint

from utils.logging.tqdm import logging_init

from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, expression_from_collection
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics, StatisticsPreValidation
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group

logging_init(
    level=logging.INFO,
    format_string="%(name)s - %(levelname)s - %(message)s",
    style="%",
)

if __name__ == "__main__":
    DATA_ID = 1

    scene_url = sample_scene_url(data_id=DATA_ID)

    collection_ndvi = expression_from_collection(
        collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI"
    )

    query_params = QueryParamsStatistics(
        url=scene_url,
        feature=sample_feature(DATA_ID),
        assets=None,  # ["nir"]
        expression=collection_ndvi.expression,  # "(nir-red)/(nir+red)"
        asset_as_band=True,
        asset_bidx=None,
        coord_crs=None,
        max_size=None,
        height=None,
        width=None,
        gsd=None,
        nodata=None,
        unscale=None,
        resampling=None,
        categorical=None,
        c=None,
        p=None,
        histogram_bins=None,
        histogram_range=None,
    )

    # Raises an AssertionError if any of the assets are not available for the query_params
    # If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics
    stats_preval = StatisticsPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)

    # Now actually request Statistics - for only arable pixels (whitelist=True)!
    stats_arable_wlist = Statistics(
        query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
        titiler_endpoint=TITILER_ENDPOINT,
        mask_enum=Sentinel2_SCL_Group.ARABLE,
        mask_asset="scl",
        whitelist=True,
    )

    pprint(stats_arable_wlist.response.json())

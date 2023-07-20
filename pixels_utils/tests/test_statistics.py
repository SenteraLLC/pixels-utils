import mock
import sure
from requests import Response

from pixels_utils.stac_catalogs.earthsearch.v1 import (
    EARTHSEARCH_SCENE_URL,
    EARTHSEARCH_URL,
    EarthSearchCollections,
    expression_from_collection,
)
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url
from pixels_utils.tests.data.utilities_testing import calculate_valid_pix_pct
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics, StatisticsPreValidation
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group

_ = sure.version


def calculate_valid_pix_pct(stats_ndvi):
    valid_pix_pct = (stats_ndvi["valid_pixels"] / (stats_ndvi["valid_pixels"] + stats_ndvi["masked_pixels"])) * 100
    return valid_pix_pct


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI_GSD_20:
    DATA_ID = 1

    FEATURE = sample_feature(DATA_ID)
    COLLECTION_NDVI = expression_from_collection(
        collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI"
    )

    URL = sample_scene_url(DATA_ID)
    EXPRESSION = COLLECTION_NDVI.expression
    ASSET_AS_BAND = True
    assets = None
    asset_bidx = None
    coord_crs = None
    max_size = None
    height = None
    width = None
    gsd = None
    nodata = None
    unscale = None
    resampling = None
    categorical = None
    c = None
    p = None
    histogram_bins = None
    histogram_range = None

    QUERY_PARAMS = QueryParamsStatistics(
        url=URL,
        feature=FEATURE,
        assets=assets,
        expression=EXPRESSION,
        asset_as_band=ASSET_AS_BAND,
        asset_bidx=asset_bidx,
        coord_crs=coord_crs,
        max_size=max_size,
        height=height,
        width=width,
        gsd=gsd,
        nodata=nodata,
        unscale=unscale,
        resampling=resampling,
        categorical=categorical,
        c=c,
        p=p,
        histogram_bins=histogram_bins,
        histogram_range=histogram_range,
    )

    def test_stats_all(self, mock_statistics_earthsearch_v1):
        name = "STATS_ALL"
        r_mock = mock_statistics_earthsearch_v1(self.DATA_ID, name)

        with mock.patch(
            "pixels_utils.titiler.endpoints.stac.Statistics.response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                query_params=self.QUERY_PARAMS,
                clear_cache=True,
                titiler_endpoint=TITILER_ENDPOINT,
                mask_enum=None,
                mask_asset=None,
                whitelist=None,
            )
            r.should.be.a(Response)
            list(r.json().keys()).should.equal(["type", "geometry", "properties"])

            data = r.json()["properties"]["statistics"]
            expression = list(r.json()["properties"]["statistics"].keys())[0]
            stats = r.json()["properties"]["statistics"][expression]

            list(stats.keys()).should.equal(
                [
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
                    "histogram",
                    "valid_percent",
                    "masked_pixels",
                    "valid_pixels",
                    "percentile_2",
                    "percentile_98",
                ]
            )
            stats["valid_percent"].should.equal(43.38, epsilon=0.01)
            stats["masked_pixels"].should.equal(1420)
            stats["valid_pixels"].should.equal(1088)
            stats["mean"].should.equal(0.1436, epsilon=0.001)
            stats["count"].should.equal(stats["valid_pixels"])
            calculate_valid_pix_pct(stats).should.equal(stats["valid_percent"], epsilon=0.01)

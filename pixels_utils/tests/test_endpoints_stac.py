import mock
import sure
from requests import Response

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.endpoints.stac import statistics
from pixels_utils.mask import SCL
from pixels_utils.tests.conftest import (
    GEOJSON_1,
    SCENE_URL_1,
    mock_endpoints_stac_statistics,
)

_ = sure.version


# def get_fixtures(geojson_aoi1_fixture, sceneid_aoi1_fixture):
#     return geojson_aoi1_fixture(), sceneid_aoi1_fixture()


def calculate_valid_pix_pct(stats_ndvi):
    valid_pix_pct = (
        stats_ndvi["valid_pixels"]
        / (stats_ndvi["valid_pixels"] + stats_ndvi["masked_pixels"])
    ) * 100
    return valid_pix_pct


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_None:
    ASSETS = None
    EXPRESSION = None
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_geo_none_scl_mask_none(self, SCENE_URL_1):
        statistics.when.called_with(
            SCENE_URL_1, assets=self.ASSETS, expression=self.EXPRESSION
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_none(self, SCENE_URL_1, GEOJSON_1):
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=GEOJSON_1,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl(self, SCENE_URL_1):
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_wl(self, SCENE_URL_1, GEOJSON_1):
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=GEOJSON_1,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_bl(self, SCENE_URL_1):
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_bl(self, SCENE_URL_1, GEOJSON_1):
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=GEOJSON_1,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl_nodata(self, SCENE_URL_1):
        NODATA = -1
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_wl_nodata(self, SCENE_URL_1, GEOJSON_1):
        NODATA = -1
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=GEOJSON_1,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_bl_nodata(self, SCENE_URL_1):
        NODATA = -1
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_bl_nodata(self, SCENE_URL_1, GEOJSON_1):
        NODATA = -1
        statistics.when.called_with(
            SCENE_URL_1,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=GEOJSON_1,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )


# r = statistics(
#     SCENE_URL,
#     assets=ASSETS,
#     expression=EXPRESSION,
#     geojson=geojson,
#     # mask_scl=MASK_SCL,
#     # whitelist=True,
# )

# f = join(
#     "/mnt/c/Users/Tyler/OneDrive - SENTERA Inc/Documents/git/pixels-utils/pixels_utils/tests/fixtures/statistics",
#     "ASSETS_None_EXPRESSION_NDVI",
#     "geo_aoi1_scl_mask_None.pickle",
# )
# with open(f, "wb") as filehandler:
#     pickle.dump(r, filehandler)

from sure import expect


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI:
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_geo_none_scl_mask_none(self, SCENE_URL_1, mock_endpoints_stac_statistics):
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_None_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                SCENE_URL_1, assets=self.ASSETS, expression=self.EXPRESSION
            )
            data = r.json()
            stats = data[self.EXPRESSION]

            r.should.be.a(Response)
            list(data.keys()).should.equal([self.EXPRESSION])
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
                    "percentile_98",
                    "percentile_2",
                ]
            )
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1786796, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_none(self, SCENE_URL_1, mock_endpoints_stac_statistics):
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_aoi1_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                SCENE_URL_1, assets=self.ASSETS, expression=self.EXPRESSION
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            stats_ndvi = stats[self.EXPRESSION]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([self.EXPRESSION])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(1420)
            stats_ndvi["mean"].should.equal(0.1435748, epsilon=0.000001)


# def test_geo_none_scl_mask_wl(self):
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=None,
#         mask_scl=self.MASK_SCL,
#         whitelist=True,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_aoi1_scl_mask_wl(self):
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=GEOJSON_1,
#         mask_scl=self.MASK_SCL,
#         whitelist=True,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_none_scl_mask_bl(self):
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=None,
#         mask_scl=self.MASK_SCL,
#         whitelist=False,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_aoi1_scl_mask_bl(self):
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=GEOJSON_1,
#         mask_scl=self.MASK_SCL,
#         whitelist=False,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_none_scl_mask_wl_nodata(self):
#     NODATA = -1
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=None,
#         mask_scl=self.MASK_SCL,
#         whitelist=True,
#         nodata=NODATA,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_aoi1_scl_mask_wl_nodata(self):
#     NODATA = -1
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=GEOJSON_1,
#         mask_scl=self.MASK_SCL,
#         whitelist=True,
#         nodata=NODATA,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_none_scl_mask_bl_nodata(self):
#     NODATA = -1
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=None,
#         mask_scl=self.MASK_SCL,
#         whitelist=False,
#         nodata=NODATA,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

# def test_geo_aoi1_scl_mask_bl_nodata(self):
#     NODATA = -1
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=GEOJSON_1,
#         mask_scl=self.MASK_SCL,
#         whitelist=False,
#         nodata=NODATA,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

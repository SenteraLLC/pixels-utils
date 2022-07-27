import mock
import sure
from requests import Request

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.endpoints.stac import statistics
from pixels_utils.mask import SCL
from pixels_utils.tests.conftest import (
    GEOJSON_1,
    SCENE_URL_1,
    mock_get_stac_statistics_geo_None_scl_mask_None_fixture,
)

_ = sure.version


# def get_fixtures(geojson_aoi1_fixture, sceneid_aoi1_fixture):
#     return geojson_aoi1_fixture(), sceneid_aoi1_fixture()


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
#     # geojson=None,
#     # mask_scl=MASK_SCL,
#     # whitelist=True,
# )

# f = join("statistics", "ASSETS_None_EXPRESSION_NDVI", "geo_None_scl_mask_None.pickle")
# with open(f, "wb") as filehandler:
#     pickle.dump(r, filehandler)


# class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI:
#     # SCENE_URL = sceneid_aoi1_fixture
#     ASSETS = None
#     EXPRESSION = EXPRESSION_NDVI
#     # GEOJSON = geojson_aoi1_fixture
#     MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

#     def test_geo_none_scl_mask_none(
#         self, SCENE_URL_1, mock_get_stac_statistics_geo_None_scl_mask_None_fixture
#     ):
#         r = mock_get_stac_statistics_geo_None_scl_mask_None_fixture(
#             assets=self.ASSETS, expression=self.EXPRESSION
#         )
#         with mock.patch(
#             "pixels_utils.endpoints.stac.statistics", return_value=r
#         ) as statistics_patch:
#             statistics_patch.return_value = r
#             statistics.when.called_with(
#                 SCENE_URL_1, assets=self.ASSETS, expression=self.EXPRESSION
#             ).should.be.a(Request)
#             # .return_value(r)


# def test_geo_aoi1_scl_mask_none(self):
#     statistics.when.called_with(
#         SCENE_URL_1,
#         assets=self.ASSETS,
#         expression=self.EXPRESSION,
#         geojson=GEOJSON_1,
#     ).should.throw(
#         ValueError,
#         "Either <assets> or <expression> must be passed.",
#     )

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

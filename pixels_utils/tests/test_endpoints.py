import mock
import sure

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.endpoints.stac import statistics
from pixels_utils.mask import SCL
from pixels_utils.tests.conftest import geojson_aoi1_fixture, sceneid_aoi1_fixture

_ = sure.version


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_None(
    sceneid_aoi1_fixture, geojson_aoi1_fixture
):
    SCENE_URL = sceneid_aoi1_fixture
    ASSETS = None
    EXPRESSION = None
    GEOJSON = geojson_aoi1_fixture
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_geo_none_scl_mask_none(self):
        statistics.when.called_with(
            self.SCENE_URL, assets=self.ASSETS, expression=self.EXPRESSION
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_none(self):
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=self.GEOJSON,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl(self):
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_wl(self):
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_bl(self):
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_bl(self):
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl_nodata(self):
        NODATA = -1
        statistics.when.called_with(
            self.SCENE_URL,
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

    def test_geo_aoi1_scl_mask_wl_nodata(self):
        NODATA = -1
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_bl_nodata(self):
        NODATA = -1
        statistics.when.called_with(
            self.SCENE_URL,
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

    def test_geo_aoi1_scl_mask_bl_nodata(self):
        NODATA = -1
        statistics.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            geojson=self.GEOJSON,
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


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI(
    sceneid_aoi1_fixture,
    geojson_aoi1_fixture,
):
    SCENE_URL = sceneid_aoi1_fixture
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    GEOJSON = geojson_aoi1_fixture
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_geo_none_scl_mask_none(
        self, mocker, mock_get_stac_statistics_geo_None_scl_mask_None_fixture
    ):
        r = mock_get_stac_statistics_geo_None_scl_mask_None_fixture(
            assets=self.ASSETS, expression=self.EXPRESSION
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r
        ) as statistics_patch:
            statistics_patch.return_value = r
            statistics.when.called_with(
                self.SCENE_URL, assets=self.ASSETS, expression=self.EXPRESSION
            ).should.return_value(r)

    # def test_geo_aoi1_scl_mask_none(self):
    #     statistics.when.called_with(
    #         self.SCENE_URL,
    #         assets=self.ASSETS,
    #         expression=self.EXPRESSION,
    #         geojson=self.GEOJSON,
    #     ).should.throw(
    #         ValueError,
    #         "Either <assets> or <expression> must be passed.",
    #     )

    # def test_geo_none_scl_mask_wl(self):
    #     statistics.when.called_with(
    #         self.SCENE_URL,
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
    #         self.SCENE_URL,
    #         assets=self.ASSETS,
    #         expression=self.EXPRESSION,
    #         geojson=self.GEOJSON,
    #         mask_scl=self.MASK_SCL,
    #         whitelist=True,
    #     ).should.throw(
    #         ValueError,
    #         "Either <assets> or <expression> must be passed.",
    #     )

    # def test_geo_none_scl_mask_bl(self):
    #     statistics.when.called_with(
    #         self.SCENE_URL,
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
    #         self.SCENE_URL,
    #         assets=self.ASSETS,
    #         expression=self.EXPRESSION,
    #         geojson=self.GEOJSON,
    #         mask_scl=self.MASK_SCL,
    #         whitelist=False,
    #     ).should.throw(
    #         ValueError,
    #         "Either <assets> or <expression> must be passed.",
    #     )

    # def test_geo_none_scl_mask_wl_nodata(self):
    #     NODATA = -1
    #     statistics.when.called_with(
    #         self.SCENE_URL,
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
    #         self.SCENE_URL,
    #         assets=self.ASSETS,
    #         expression=self.EXPRESSION,
    #         geojson=self.GEOJSON,
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
    #         self.SCENE_URL,
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
    #         self.SCENE_URL,
    #         assets=self.ASSETS,
    #         expression=self.EXPRESSION,
    #         geojson=self.GEOJSON,
    #         mask_scl=self.MASK_SCL,
    #         whitelist=False,
    #         nodata=NODATA,
    #     ).should.throw(
    #         ValueError,
    #         "Either <assets> or <expression> must be passed.",
    #     )

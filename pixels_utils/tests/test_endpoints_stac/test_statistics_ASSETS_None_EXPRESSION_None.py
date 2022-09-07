import sure

from pixels_utils.endpoints.stac import statistics_response
from pixels_utils.mask import SCL
from pixels_utils.tests.data.load_data import sample_geojson, sample_scene_url

_ = sure.version


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_None_GSD_20:
    ASSETS = None
    EXPRESSION = None
    GSD = 20
    RESAMPLING = "nearest"
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
    SCENE_URL = sample_scene_url(data_id=1)
    GEOJSON = sample_geojson(data_id=1)

    def test_geo_none_scl_mask_none(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_none(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=self.GEOJSON,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_wl(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_bl(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=None,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_aoi1_scl_mask_bl(self):
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

    def test_geo_none_scl_mask_wl_nodata(self):
        NODATA = -1
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
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
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
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
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
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
        statistics_response.when.called_with(
            self.SCENE_URL,
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            resampling=self.RESAMPLING,
            geojson=self.GEOJSON,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            nodata=NODATA,
        ).should.throw(
            ValueError,
            "Either <assets> or <expression> must be passed.",
        )

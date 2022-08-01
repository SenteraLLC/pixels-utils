import mock
import sure
from requests import Response

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.endpoints.stac import statistics
from pixels_utils.mask import SCL, build_numexpr_scl_mask
from pixels_utils.tests.conftest import (
    GEOJSON_FIXTURE,
    SCENE_URL_FIXTURE,
    mock_endpoints_stac_statistics,
)
from pixels_utils.tests.data.load_data import (
    sample_aoi,
    sample_scene_url,
    sample_sceneid,
)

_ = sure.version


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
    SCENE_URL = sample_scene_url(data_id=1)
    GEOJSON = sample_aoi(data_id=1)

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


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI:
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
    SCENE_URL = sample_scene_url(data_id=1)
    GEOJSON = sample_aoi(data_id=1)

    def test_geo_none_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_None_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=None,
                mask_scl=MASK_SCL,
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

    def test_geo_aoi1_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_aoi1_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=self.GEOJSON,
                mask_scl=MASK_SCL,
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

    def test_geo_none_scl_mask_wl(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = 0.0
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_None_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.0214196, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_wl(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = 0.0
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_aoi1_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(
                1487
            )  # TODO: why is this different from other aoi1?
            stats_ndvi["mean"].should.equal(0.1438003, epsilon=0.000001)

    def test_geo_none_scl_mask_bl(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = 0.0
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_None_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1572600, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_bl(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = 0.0
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_aoi1_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(
                1487
            )  # TODO: why is this different from other aoi1?
            stats_ndvi["mean"].should.equal(0.0, epsilon=0.000001)

    def test_geo_none_scl_mask_wl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            fname_pickle=f"geo_None_scl_mask_wl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(-0.9236173, epsilon=0.000001)


# from pixels_utils.tests.data.load_data import sample_aoi, sample_scene_url

# DATA_ID = 1
# GEOJSON = sample_aoi(DATA_ID)["features"][0]
# MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
# ASSETS = None
# EXPRESSION = EXPRESSION_NDVI


# r = statistics(
#     sample_scene_url(1),
#     assets=ASSETS,
#     expression=EXPRESSION,
#     geojson=None,  # GEOJSON
#     mask_scl=MASK_SCL, # MASK_SCL,
#     whitelist=WHITELIST,
#     nodata=NODATA,
# )
# r.json()


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

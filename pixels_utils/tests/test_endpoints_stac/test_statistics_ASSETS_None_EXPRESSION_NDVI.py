import mock
import sure
from requests import Response

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.mask import SCL, build_numexpr_scl_mask
from pixels_utils.stac_endpoint import statistics_response
from pixels_utils.tests.conftest import mock_endpoints_stac_statistics
from pixels_utils.tests.data.load_data import sample_geojson, sample_scene_url
from pixels_utils.tests.data.utilities_testing import calculate_valid_pix_pct

_ = sure.version


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI_GSD_20:
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    GSD = 20
    RESAMPLING = "nearest"
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
    SCENE_URL = sample_scene_url(data_id=1)
    GEOJSON = sample_geojson(data_id=1)

    def test_geo_none_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        WHITELIST = None
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
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
                    "percentile_2",
                    "percentile_98",
                ]
            )
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1786796, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        WHITELIST = None
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
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
            stats_ndvi["masked_pixels"].should.equal(
                363
            )  # TODO: why is this 363, but others are 375? The others are masked, but why does that matter if they are all soil + vegetation?
            stats_ndvi["mean"].should.equal(0.1437814, epsilon=0.000001)

    def test_geo_none_scl_mask_wl(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
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
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(375)
            stats_ndvi["mean"].should.equal(0.1438418, epsilon=0.000001)

    def test_geo_none_scl_mask_bl(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
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
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(375)
            nodata_bl = 0.0 if NODATA is None else NODATA
            stats_ndvi["mean"].should.equal(nodata_bl, epsilon=0.000001)

    def test_geo_none_scl_mask_wl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_wl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(-0.9236173, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_wl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_wl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(375)
            stats_ndvi["mean"].should.equal(0.1438418, epsilon=0.000001)

    def test_geo_none_scl_mask_bl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_bl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1022969, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_bl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_bl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(375)
            nodata_bl = 0.0 if NODATA is None else NODATA
            stats_ndvi["mean"].should.equal(nodata_bl, epsilon=0.000001)


class Test_Endpoint_Stac_Statistics_ASSETS_None_EXPRESSION_NDVI_GSD_10:
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    GSD = 10
    RESAMPLING = "nearest"
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
    SCENE_URL = sample_scene_url(data_id=1)
    GEOJSON = sample_geojson(data_id=1)

    def test_geo_none_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        WHITELIST = None
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data[self.EXPRESSION]

            r.should.be.a(Response)
            list(data.keys()).should.equal([self.EXPRESSION])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1786796, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_none(self, mock_endpoints_stac_statistics):
        MASK_SCL = None
        WHITELIST = None
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_None.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
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
            stats_ndvi["masked_pixels"].should.equal(
                1495.0
            )  # TODO: why is this 1495, but others are 1543? The others are masked, but why does that matter if they are all soil + vegetation?
            stats_ndvi["mean"].should.equal(0.1438459, epsilon=0.000001)

    def test_geo_none_scl_mask_wl(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
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
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_wl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(1543.0)
            stats_ndvi["mean"].should.equal(0.1437667, epsilon=0.000001)

    def test_geo_none_scl_mask_bl(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
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
        NODATA = None
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_bl.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(1543.0)
            nodata_bl = 0.0 if NODATA is None else NODATA
            stats_ndvi["mean"].should.equal(nodata_bl, epsilon=0.000001)

    def test_geo_none_scl_mask_wl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_wl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(-0.9236173, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_wl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = True
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_wl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(1543.0)
            stats_ndvi["mean"].should.equal(0.1437667, epsilon=0.000001)

    def test_geo_none_scl_mask_bl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_None_scl_mask_bl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=None,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats = data[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal([key])
            stats["count"].should.equal(stats["valid_pixels"])
            stats["valid_percent"].should.equal(100.0, epsilon=0.01)
            stats["masked_pixels"].should.equal(0)
            stats["mean"].should.equal(0.1022969, epsilon=0.000001)

    def test_geo_aoi1_scl_mask_bl_nodata(self, mock_endpoints_stac_statistics):
        WHITELIST = False
        NODATA = -1
        r_mock = mock_endpoints_stac_statistics(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            gsd=self.GSD,
            fname_pickle=f"geo_aoi1_scl_mask_bl_nodata.pickle",
        )
        with mock.patch(
            "pixels_utils.endpoints.stac.statistics_response", return_value=r_mock
        ) as statistics_patch:
            r = statistics_patch(
                self.SCENE_URL,
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                gsd=self.GSD,
                resampling=self.RESAMPLING,
                geojson=self.GEOJSON,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                nodata=NODATA,
            )
            data = r.json()
            stats = data["properties"]["statistics"]
            key = build_numexpr_scl_mask(
                assets=self.ASSETS,
                expression=self.EXPRESSION,
                mask_scl=self.MASK_SCL,
                whitelist=WHITELIST,
                mask_value=NODATA,
            )[:-1]
            stats_ndvi = stats[key]

            r.should.be.a(Response)
            list(data.keys()).should.equal(["type", "geometry", "properties", "id"])
            list(stats.keys()).should.equal([key])

            stats_ndvi["count"].should.equal(stats_ndvi["valid_pixels"])
            stats_ndvi["valid_percent"].should.equal(
                calculate_valid_pix_pct(stats_ndvi), epsilon=0.01
            )
            stats_ndvi["masked_pixels"].should.equal(1543.0)
            nodata_bl = 0.0 if NODATA is None else NODATA
            stats_ndvi["mean"].should.equal(nodata_bl, epsilon=0.000001)


# from pixels_utils.tests.data.load_data import sample_geojson, sample_scene_url

# DATA_ID = 1
# GEOJSON = sample_geojson(DATA_ID)
# MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]
# ASSETS = None
# EXPRESSION = EXPRESSION_NDVI
# GSD = 10
# RESAMPLING = "nearest"

# GEOJSON = sample_geojson(DATA_ID)
# MASK_SCL = None  # [SCL.VEGETATION, SCL.BARE_SOIL]
# WHITELIST = None
# NODATA = None

# r = statistics(
#     sample_scene_url(1),
#     assets=ASSETS,
#     expression=EXPRESSION,
#     geojson=GEOJSON,
#     mask_scl=MASK_SCL,
#     whitelist=WHITELIST,
#     nodata=NODATA,
#     gsd=GSD,
#     resampling=RESAMPLING,
# )
# r.json()
# data = r.json()
# stats = data["properties"]["statistics"]
# key = build_numexpr_scl_mask(
#     assets=ASSETS,
#     expression=EXPRESSION,
#     mask_scl=MASK_SCL,
#     whitelist=WHITELIST,
#     nodata=NODATA,
# )[:-1]
# stats_ndvi = stats[key]

# # gsd = 20
# #  'mean': 0.14384179354016094,
# #  'count': 265.0,
# #  'sum': 38.11807528814265,
# #  'std': 0.010827744028599791,
# #  'median': 0.14557889594528578,

# # gsd = 10
#  'mean': 0.14376671636810673,
#  'count': 1081.0,
#  'sum': 155.41182039392336,
#  'std': 0.012831036107724774,
#  'median': 0.14442916093535077,

# # gsd = None
#  'mean': 0.14380032393285688,
#  'count': 1021.0,
#  'sum': 146.82013073544687,
#  'std': 0.0121265938833696,
#  'median': 0.14462416745956233,

# from pixels_utils.utilities import get_assets_expression_query

# query, _ = get_assets_expression_query(
#     sample_scene_url(1),
#     assets=ASSETS,
#     expression=EXPRESSION,
#     mask_scl=MASK_SCL,
#     whitelist=WHITELIST,
#     nodata=NODATA,
# )

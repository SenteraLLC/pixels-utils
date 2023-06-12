import mock
import sure
from pandas import DataFrame

from pixels_utils.scenes import parse_nested_stac_data, search_stac_scenes
from pixels_utils.tests.conftest import mock_scenes_earthsearch_v1
from pixels_utils.tests.data.load_data import sample_feature

_ = sure.version


class Test_Scenes:
    GEOJSON = sample_feature(data_id=1)

    def test_search_stac_scenes(self, mock_scenes_earthsearch_v1):
        from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

        r_mock = mock_scenes_earthsearch_v1(
            fname_pickle="CLOUD-80_GEOM-1_MONTH-6.pickle",
        )
        with mock.patch("pixels_utils.scenes.search_stac_scenes", return_value=r_mock) as search_stac_scenes_patch:
            df_scenes = search_stac_scenes_patch(
                geometry=self.GEOJSON,
                date_start="2022-06-01",
                date_end="2022-06-30",
                stac_catalog_url=EARTHSEARCH_URL,
                collection=EarthSearchCollections,
                query={"eo:cloud_cover": {"lt": 80}},
                simplify_to_bbox=True,
            )
            df_scenes.should.be.a(DataFrame)
            list(df_scenes.columns).should.be.equal_to(
                [
                    "type",
                    "stac_version",
                    "id",
                    "properties",
                    "geometry",
                    "links",
                    "assets",
                    "bbox",
                    "stac_extensions",
                    "collection",
                    "datetime",
                    "eo:cloud_cover",
                ]
            )

    def test_parse_nested_stac_data(self, mock_scenes_earthsearch_v1):
        from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

        r_mock = mock_scenes_earthsearch_v1(
            fname_pickle="CLOUD-80_GEOM-1_MONTH-6.pickle",
        )
        with mock.patch("pixels_utils.scenes.search_stac_scenes", return_value=r_mock) as search_stac_scenes_patch:
            df_scenes = search_stac_scenes_patch(
                geometry=self.GEOJSON,
                date_start="2022-06-01",
                date_end="2022-06-30",
                stac_catalog_url=EARTHSEARCH_URL,
                collection=EarthSearchCollections,
                query={"eo:cloud_cover": {"lt": 80}},
                simplify_to_bbox=True,
            )
            df_properties = parse_nested_stac_data(df=df_scenes, column="properties")
            len(df_scenes).should.equal(len(df_properties))

            df_assets = parse_nested_stac_data(df=df_scenes, column="assets")
            len(df_scenes).should.equal(len(df_assets))

            df_assets = parse_nested_stac_data(df=df_scenes, column="assets")
            len(df_scenes).should.equal(len(df_assets))

    def test_request_asset_info(self, mock_scenes_earthsearch_v1, mock_scene_asset_info_earthsearch_v1):
        from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections

        r_mock_scenes = mock_scenes_earthsearch_v1(
            fname_pickle="CLOUD-80_GEOM-1_MONTH-6.pickle",
        )
        r_mock_asset_info = mock_scene_asset_info_earthsearch_v1(
            fname_pickle="CLOUD-80_GEOM-1_MONTH-6_asset-info.pickle",
        )
        with mock.patch(
            "pixels_utils.scenes.search_stac_scenes", return_value=r_mock_scenes
        ) as search_stac_scenes_patch:
            df_scenes = search_stac_scenes_patch(
                geometry=self.GEOJSON,
                date_start="2022-06-01",
                date_end="2022-06-30",
                stac_catalog_url=EARTHSEARCH_URL,
                collection=EarthSearchCollections,
                query={"eo:cloud_cover": {"lt": 80}},
                simplify_to_bbox=True,
            )
            with mock.patch(
                "pixels_utils.scenes.request_asset_info", return_value=r_mock_asset_info
            ) as request_asset_info_patch:
                df_asset_info = request_asset_info_patch(df=df_scenes)
                len(df_scenes).should.equal(len(df_asset_info))

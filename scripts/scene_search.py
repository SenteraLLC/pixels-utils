from pixels_utils.scenes import parse_nested_stac_data, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections
from pixels_utils.tests.data.load_data import sample_feature

if __name__ == "__main__":
    DATA_ID = 1

    df_scenes = search_stac_scenes(
        geometry=sample_feature(DATA_ID),
        date_start="2019-01-01",
        date_end="2019-01-31",
        stac_catalog_url=EARTHSEARCH_URL,
        collection=EarthSearchCollections.sentinel_2_l2a,
        query={"eo:cloud_cover": {"lt": 80}},  # keeps less than 80% cloud cover,
        simplify_to_bbox=True,
    )

    print(
        df_scenes[["id"]]
        .merge(
            parse_nested_stac_data(df=df_scenes, column="properties")[["datetime", "eo:cloud_cover"]],
            left_index=True,
            right_index=True,
        )
        .to_markdown(tablefmt="pipe")
    )

from dataclasses import InitVar, dataclass
from enum import Enum, auto
from functools import cached_property
from typing import Dict, Optional, Tuple, Union

from pandas import DataFrame
from requests import get

from pixels_utils.stac_catalogs.earthsearch import AutoDashNameEnum

EARTHSEARCH_URL = "https://earth-search.aws.element84.com/v1"
EARTHSEARCH_COLLECTION_URL = f"{EARTHSEARCH_URL}" "/collections/{collection}"
EARTHSEARCH_SCENE_URL = f"{EARTHSEARCH_URL}" "/collections/{collection}/items/{id}"


class EarthSearchCollections(AutoDashNameEnum):
    cop_dem_glo_30 = auto()
    naip = auto()
    sentinel_2_l2a = auto()
    sentinel_2_l1c = auto()
    landsat_c2_l2 = auto()
    cop_dem_glo_90 = auto()
    sentinel_1_grd = auto()

    def equals(self, string):
        if isinstance(string, Enum):
            string = string.name
        return self.name == string


@dataclass
class STACMetaData:
    """
    Dataclass for extracting the metadata properties of the collection's assets.

    Example:
        >>> from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, STACMetaData
        >>> stac_metadata = STACMetaData(collection=EarthSearchCollections.sentinel_2_l2a, assets=("blue",))
        >>> stac_metadata.asset_names
        >>> stac_metadata.asset_titles
        >>> stac_metadata.df_assets
        >>> [a.name for a in stac_metadata.AssetNames]
        >>> stac_metadata.parse_asset_bands(column_name="raster:bands", return_dataframe=True)
        >>> stac_metadata.parse_asset_bands(column_name="raster:bands", return_dataframe=False)
        >>> stac_metadata.df_assets[stac_metadata.df_assets["name"] == "blue"]["raster:bands"]
        >>> stac_metadata.parse_asset_bands(column_name="eo:bands", return_dataframe=True)
        >>> stac_metadata.parse_asset_bands(column_name="eo:bands", return_dataframe=False)
    """

    collection: str
    assets: InitVar[Optional[Tuple]] = None

    def __post_init__(self, assets):
        self.assets = assets
        self.collection = (
            self.collection.name if isinstance(self.collection, EarthSearchCollections) else self.collection
        )
        self.url = EARTHSEARCH_COLLECTION_URL.format(collection=self.collection)
        self.metadata_full = get(self.url).json()

        # Runs each of the cached_propreties on class declaration
        self.asset_names
        self.asset_titles
        self.df_assets
        self.AssetNames = Enum("AssetNames", self.asset_names)

    @cached_property
    def asset_names(self) -> Tuple:
        names = (
            tuple([k for k in self.metadata_full["item_assets"].keys()])
            if self.assets is None
            else tuple([k for k in self.metadata_full["item_assets"].keys() if k in self.assets])
        )
        seen = set()
        dupes = set(x for x in names if x in seen or seen.add(x))
        if len(dupes) > 0:
            raise ValueError(
                "STACMetaData dataclass assumes unique asset names. Found the following duplicate "
                f"asset_names: {tuple(dupes)}"
            )
        return names

    # TODO: Put this function in another file to keep code low
    def _filter_item_assets(
        self,
    ):
        return (
            self.metadata_full["item_assets"]
            if self.assets is None
            else {
                k: self.metadata_full["item_assets"][k] for k in self.metadata_full["item_assets"] if k in self.assets
            }
        )

    @cached_property
    def asset_titles(self) -> Tuple:
        item_assets = self._filter_item_assets()
        return tuple([item_assets[a]["title"] for a in item_assets if "title" in item_assets[a].keys()])

    @cached_property
    def df_assets(self) -> DataFrame:
        item_assets = self._filter_item_assets()
        asset_info = [dict(item_assets[k], **{"name": k}) for k in item_assets]
        df = DataFrame.from_records(asset_info)
        df.insert(0, "name", df.pop("name"))
        return df

    # TODO: probably make a wrapper for this function to keep code low in v1.py
    def parse_asset_bands(
        self, column_name: str = "raster:bands", return_dataframe: bool = False
    ) -> Union[DataFrame, Dict]:
        # column_name = "raster:bands"  # or "eo:bands"
        assert (
            column_name in self.df_assets.columns
        ), f'"{column_name}" is not a property of the {self.collection} collection.'

        asset_bands = [
            dict(j, **{"name": self.df_assets.iloc[i]["name"]})
            for i, k in enumerate(self.df_assets[column_name])
            if isinstance(k, list)
            for j in k
            if isinstance(j, dict)
        ]

        asset_bands_null = [
            dict({}, **{"name": self.df_assets.iloc[i]["name"]})
            for i, k in enumerate(self.df_assets[column_name])
            if isinstance(k, float)  # indicates k is NULL
        ]
        if return_dataframe:
            return DataFrame.from_records(asset_bands + asset_bands_null)
        else:
            return asset_bands + asset_bands_null

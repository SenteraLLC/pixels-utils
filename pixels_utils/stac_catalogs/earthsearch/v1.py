from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import Dict, Tuple, Union

from pandas import DataFrame, isnull
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
        >>> from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, STAC_MetaData
        >>> c = STAC_MetaData(collection=EarthSearchCollections.sentinel_2_l2a)
        >>> c.asset_names
        >>> c.asset_titles
        >>> c.df_assets
        >>> c.parse_raster_bands(name="blue", return_dataframe=True)
        >>> c.parse_raster_bands(name="blue", return_dataframe=False)
        >>> c.df_assets[c.df_assets["name"] == "blue"]["raster:bands"]
        >>> c.parse_eo_bands(name="visual", return_dataframe=True)
        >>> c.parse_eo_bands(name="visual", return_dataframe=False)
    """

    collection: str

    def __post_init__(self):
        self.collection = (
            self.collection.name if isinstance(self.collection, EarthSearchCollections) else self.collection
        )
        self.url = EARTHSEARCH_COLLECTION_URL.format(collection=self.collection)
        self.metadata_full = get(self.url).json()

        # Runs each of the cached_propreties on class declaration
        self.asset_names
        self.asset_titles
        self.df_assets

    @cached_property
    def asset_names(self) -> Tuple:
        names = tuple(self.metadata_full["item_assets"].keys())
        seen = set()
        dupes = set(x for x in names if x in seen or seen.add(x))
        if len(dupes) > 0:
            raise ValueError(
                "EarthSearchCollection dataclass assumes unique asset names. Found the following duplicate "
                f"asset_names: {tuple(dupes)}"
            )
        return names

    @cached_property
    def asset_titles(self) -> Tuple:
        assets = self.metadata_full["item_assets"]
        return tuple([assets[a]["title"] for a in assets if "title" in assets[a].keys()])

    @cached_property
    def df_assets(self) -> DataFrame:
        assets = self.metadata_full["item_assets"]
        asset_info = [dict(assets[k], **{"name": k}) for k in assets]
        df = DataFrame.from_records(asset_info)
        df.insert(0, "name", df.pop("name"))
        return df

    def parse_raster_bands(self, name: str, return_dataframe: bool = False) -> Union[DataFrame, Dict]:
        col = "raster:bands"
        assert col in self.df_assets.columns, f'"{col}" is not a property of the {self.collection} collection.'
        assert name in self.df_assets["name"].unique()
        df_filter = self.df_assets[self.df_assets["name"] == name]
        if any(isnull(df_filter[col])):
            raise ValueError(f'Asset "{name}" is null; cannot parse raster:bands.')
        raster_bands = df_filter[col].item() if len(df_filter[col]) == 1 else df_filter[col]
        if return_dataframe:
            return DataFrame.from_records(raster_bands)
        else:
            return raster_bands

    def parse_eo_bands(self, name: str, return_dataframe: bool = False) -> Dict:
        col = "eo:bands"
        assert col in self.df_assets.columns, f'"{col}" is not a property of the {self.collection} collection.'
        assert name in self.df_assets["name"].unique()
        df_filter = self.df_assets[self.df_assets["name"] == name]
        if any(isnull(df_filter[col])):
            raise ValueError(f'Asset "{name}" is null; cannot parse eo:bands.')
        eo_bands = df_filter[col].item() if len(df_filter[col]) == 1 else df_filter[col]
        if return_dataframe:
            return DataFrame.from_records(eo_bands)
        else:
            return eo_bands

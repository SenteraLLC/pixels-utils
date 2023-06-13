import logging
from dataclasses import InitVar, dataclass
from enum import Enum
from functools import cached_property
from typing import Dict, Optional, Tuple, Union

from pandas import DataFrame
from requests import get


def _filter_item_assets(
    assets,
    metadata_full,
    asset_item_key,
):
    return (
        metadata_full[asset_item_key]
        if assets is None
        else {k: metadata_full[asset_item_key][k] for k in metadata_full[asset_item_key] if k in assets}
    )


@dataclass
class STACMetaData:
    """
    Dataclass for extracting the metadata properties of the collection's assets.

    Example:
        >>> from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, EARTHSEARCH_COLLECTION_URL, STACMetaData
        >>> stac_metadata = STACMetaData(collection=EarthSearchCollections.sentinel_2_l2a, assets=("blue", "green", "red", "rededge1", "rededge2"))
        >>> stac_metadata = STACMetaData(collection_url=EARTHSEARCH_COLLECTION_URL.format(collection=EarthSearchCollections.sentinel_2_l2a.name), assets=("scl", "blue", "green", "red", "rededge1", "rededge2",))
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

    collection_url: str
    assets: InitVar[Optional[Tuple]] = None
    asset_item_key: InitVar[Optional[str]] = "item_assets"
    asset_title_key: InitVar[Optional[str]] = "title"

    def __post_init__(self, assets, asset_item_key, asset_title_key):
        self.assets = assets
        self.ASSET_ITEM_KEY = asset_item_key
        self.ASSET_TITLE_KEY = asset_title_key
        self.metadata_full = get(self.collection_url).json()

        # Runs each of the cached_propreties on class declaration
        self.asset_names
        self._validate_assets()
        self.asset_titles
        self.df_assets
        self.AssetNames = Enum("AssetNames", self.asset_names)

    def _validate_assets(self):
        if self.assets is not None:
            if set(self.assets) != set(self.asset_names):
                invalid_assets = list(set(self.assets) - set(self.asset_names))
                logging.warning(
                    "Some assets passed to STACMetaData are invalid. Invalid assets are being removed from the assets "
                    "property and include: %s",
                    invalid_assets,
                )
        self.assets = self.asset_names  # Sync up assets and asset_names regardless

    @cached_property
    def asset_names(self) -> Tuple:
        names = (
            tuple([k for k in self.metadata_full[self.ASSET_ITEM_KEY].keys()])
            if self.assets is None
            else tuple([k for k in self.metadata_full[self.ASSET_ITEM_KEY].keys() if k in self.assets])
        )
        seen = set()
        dupes = set(x for x in names if x in seen or seen.add(x))
        if len(dupes) > 0:
            raise ValueError(
                "STACMetaData dataclass assumes unique asset names. Found the following duplicate "
                f"asset names: {tuple(dupes)}"
            )
        return names

    @cached_property
    def asset_titles(self) -> Tuple:
        item_assets = _filter_item_assets(
            assets=self.assets, metadata_full=self.metadata_full, asset_item_key=self.ASSET_ITEM_KEY
        )
        return tuple(
            [item_assets[a][self.ASSET_TITLE_KEY] for a in item_assets if self.ASSET_TITLE_KEY in item_assets[a].keys()]
        )

    @cached_property
    def df_assets(self) -> DataFrame:
        item_assets = _filter_item_assets(
            assets=self.assets, metadata_full=self.metadata_full, asset_item_key=self.ASSET_ITEM_KEY
        )
        asset_info = [dict(item_assets[k], **{"name": k}) for k in item_assets]
        df = DataFrame.from_records(asset_info)
        df.insert(0, "name", df.pop("name"))
        return df

    # TODO: probably make a wrapper for this function to keep code low in v1.py
    def parse_asset_bands(
        self, column_name: str = "raster:bands", return_dataframe: bool = False
    ) -> Union[DataFrame, Dict]:
        """
        Parses a nested dictionary of asset band information.

        Args:
            column_name (str, optional): Column of self.df_assets to parse (must be a nested dictionary). Defaults to
            "raster:bands".

            return_dataframe (bool, optional): Whether to return result as a `dict` (`return_dataframe=False`) or
            `DataFrame` (`return_dataframe=True`). Defaults to False.

        Returns:
            Union[DataFrame, Dict]: Parsed asset band information, either as a `dict` or `DataFrame`.
        """
        assert (
            column_name in self.df_assets.columns
        ), f'"{column_name}" is not a property of the "{self.collection_url.split("/")[-1]}" collection; choose from {list(self.df_assets.columns)}.'
        # col_dtype = self.df_assets[column_name].dtype
        # assert col_dtype == dict, f'"{column_name}" must be "dict" dtype; got "{col_dtype}" instead.'

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

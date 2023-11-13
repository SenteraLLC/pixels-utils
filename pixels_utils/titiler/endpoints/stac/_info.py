import logging
from functools import cached_property
from typing import ClassVar, List, Tuple, Type

from joblib import Memory  # type: ignore
from marshmallow import Schema, ValidationError, validates
from marshmallow_dataclass import dataclass
from pandas import DataFrame
from requests import get
from retry import retry

from pixels_utils.stac_metadata import STACMetaData
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints import STAC_ENDPOINT
from pixels_utils.titiler.endpoints.stac._connect import online_status_stac
from pixels_utils.titiler.endpoints.stac._utilities import validate_assets
from pixels_utils.titiler.endpoints.stac.types import STAC_info

STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"
QUERY_ASSETS = "assets"
QUERY_URL = "url"

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@dataclass  # from marshmallow_dataclass
class QueryParamsInfo:
    url: str
    assets: List[str] = None
    Schema: ClassVar[Type[Schema]] = Schema

    @validates(field_name="assets")
    def validate_coord_crs(self, assets):
        if assets is not None and isinstance(assets, str):
            raise ValidationError('"assets" must be a list of strings.')
            # TODO: How to set `data["assets"] = [data["assets"]] if isinstance(data["assets"], str) else data["assets"]``


@retry((ConnectionError, KeyError, RuntimeError), tries=3, delay=2)
class Info:
    """
    Class to help faciilitate titiler STAC info endpoint.

    For more information, refer to [Titiler](https://developmentseed.org/titiler/endpoints/stac/#info) and
    [STAC](https://stacspec.org/en/about/stac-spec/).

    See a list of available assets for the EarthSearch collections in this Confluence page:
    https://sentera.atlassian.net/wiki/spaces/GML/pages/3357278209/EarthSearch+Collection+Availability

    Example:
        https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01

    Args:
        url (str): STAC item URL; the `https://somewhere.com/item.json` part of the example URL above.
        assets (Tuple[str], optional): Asset names; the `B01` part of the example URL above. Defaults to all available
        assets.

        titiler_endpoint (str): The `https://myendpoint` part of the example URL above. Defaults to
        `https://pixels.sentera.com/stac/info`.

        check_individual_asset_availability (bool): Whether to individually check availability of assets (in `url`)
        during __init__(). If True, loops through `assets` and runs `is_asset_available()` on each; if False, simply
        checks whether `assets` is a subset of `asset_names`. Defaults to False. Whether to validate each asset
        individually during __init__(). Defaults to True.
    """

    def __init__(
        self,
        url: str,
        assets: Tuple[str] = None,
        titiler_endpoint: str = TITILER_ENDPOINT,
        check_individual_asset_availability: bool = True,
    ):
        self.url = url
        self.assets = assets
        self.titiler_endpoint = titiler_endpoint
        self.asset_metadata  # Runs cached_property on class declaration
        self.assets_valid = validate_assets(
            assets=self.assets,
            asset_names=self.asset_metadata.asset_names,
            check_individual_asset_availability=check_individual_asset_availability,
            url=self.url,
            stac_info_endpoint=STAC_INFO_ENDPOINT,
        )

        self.response  # Should run after asset_metadata to validate assets

    @cached_property
    def response(
        self,
    ) -> STAC_info:
        """
        Return basic info on STAC item's COG.

        Returns:
            STAC_info: Response from the titiler stac info endpoint.
        """
        online_status_stac(self.titiler_endpoint, stac_endpoint=self.url)
        query = {
            QUERY_URL: self.url,
            QUERY_ASSETS: self.assets_valid,
        }
        r = get(
            STAC_INFO_ENDPOINT,
            params=query,
        )
        if r.status_code != 200:
            logging.warning("Info GET request failed. Reason: %s", r.reason)
        return STAC_info(r)

    def _parse_collection_url(self, url: str) -> str:
        assert "/collections/" in url, '"/collections/" must be part of the STAC url.'
        earthsearch_url, collection_scene_url = url.split("/collections/")
        return earthsearch_url + "/collections/" + collection_scene_url.split("/")[0]

    @cached_property
    def asset_metadata(self) -> DataFrame:
        """
        Retrieves asset metadata made available by the STAC collection.

        Return:
            DataFrame: STAC asset metadata.
        """

        return STACMetaData(collection_url=self._parse_collection_url(self.url), assets=self.assets)

    def to_dataframe(self) -> DataFrame:
        """
        Parses self.response.json() to pandas DataFrame

        Return:
            DataFrame: Titiler STAC info response.
        """
        assert (
            self.response.status_code == 200
        ), f"Cannot convert response.json() to pandas DataFrame. Reason: {self.response.reason}."
        info = self.response.json()
        info_list = [dict(info[k], **{"name": k}) for k in info]
        df = DataFrame.from_records(info_list)
        df.insert(0, "name", df.pop("name"))
        return df

    @cached_property
    def df_nodata(self) -> DataFrame:
        """
        If available, returns a dataframe with a "nodata" column indicating the nodata value for each asset.

        Returns None if nodata information cannot be found.

        Assumes nodata information is stored in the "raster:bands" column of the STAC asset metadata. If a collection
        does not have a "raster:bands" column, this method will log a warning and return None.

        Although idea is good, this may be a function best left up to the user, as it is not always clear which column
        might contain the nodata value. For example, the "eo:bands" column may contain the nodata value for some assets
        while "raster:bands" may contain the nodata value for other assets.
        """
        # TODO: Check if "nodata" can be found nested in any of the self.asset_metadata.df_assets columns
        if "raster:bands" in self.asset_metadata.df_assets.columns:
            raster_bands = self.asset_metadata.parse_asset_bands(column_name="raster:bands", return_dataframe=True)
            if "nodata" in raster_bands.columns:
                return raster_bands
        elif "eo:bands" in self.asset_metadata.df_assets.columns:
            eo_bands = self.asset_metadata.parse_asset_bands(column_name="eo:bands", return_dataframe=True)
            if "nodata" in eo_bands.columns:
                return eo_bands
        # TODO: elif any other places the might contain nodata information for assets
        else:
            logging.warning("Unable to determine nodata value for url %s.", self.url)
            return None

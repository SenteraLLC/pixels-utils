import logging
from functools import cached_property
from typing import NewType, Tuple

from joblib import Memory  # type: ignore
from pandas import DataFrame
from requests import Response, get
from retry import retry

from pixels_utils.stac_metadata import STACMetaData
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac._connect import online_status_stac
from pixels_utils.titiler.endpoints.stac._constants import STAC_ENDPOINT

STAC_info = NewType("STAC_info", Response)
STAC_INFO_ENPOINT = f"{STAC_ENDPOINT}/info"
QUERY_ASSETS = "assets"
QUERY_URL = "url"

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
class Info:
    """
    Class to help faciilitate titiler "info" endpoint (https://developmentseed.org/titiler/endpoints/stac/#info).

    Example:
        https://myendpoint/stac/info?url=https://somewhere.com/item.json&assets=B01

    Args:
        url (str): STAC item URL; the `https://somewhere.com/item.json` part of the example URL above.
        assets (Tuple[str], optional): Asset names; the `B01` part of the example URL above. Defaults to all available
        assets.

        titiler_endpoint (str): The `https://myendpoint` part of the example URL above. Defaults to
        `https://pixels.sentera.com/stac/info`.
    """

    def __init__(self, url: str, assets: Tuple[str] = None, titiler_endpoint: str = TITILER_ENDPOINT):
        self.url = url
        self.assets = assets
        self.titiler_endpoint = titiler_endpoint
        self.asset_metadata  # Runs cached_property on class declaration
        self._validate_assets()
        self.response  # Should run after asset_metadata to validate assets

    def _validate_assets(self):
        if set(self.assets) != set(self.asset_metadata.asset_names):
            invalid_assets = list(set(self.assets) - set(self.asset_metadata.asset_names))
            logging.warning(
                "Some assets passed to the Info endpoint are invalid. Invalid assets are being removed from the assets "
                "property and include: %s",
                invalid_assets,
            )
            self.assets = self.asset_metadata.asset_names

    @cached_property
    def response(
        self,
    ) -> STAC_info:
        """
        Return basic info on STAC item's COG.

        Returns:
            STAC_info: _description_
        """
        online_status_stac(self.titiler_endpoint, stac_endpoint=self.url)
        self._validate_assets()  # Validate again in case anything changed since class declaration

        query = {
            QUERY_URL: self.url,
            QUERY_ASSETS: self.assets,
        }
        r = get(
            STAC_INFO_ENPOINT,
            params=query,
        )
        if r.status_code != 200:
            logging.warning("Info GET request failed. Reason: %s", r.reason)
        return r

    @cached_property
    def asset_metadata(self) -> DataFrame:
        """
        Retrieves asset metadata made available by the STAC collection.

        Return:
            DataFrame: STAC asset metadata.
        """

        def _parse_collection_url(url: str) -> str:
            assert "/collections/" in url, '"/collections/" must be part of the STAC url.'
            earthsearch_url, collection_scene_url = url.split("/collections/")
            return earthsearch_url + "/collections/" + collection_scene_url.split("/")[0]

        return STACMetaData(collection_url=_parse_collection_url(self.url), assets=self.assets)

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

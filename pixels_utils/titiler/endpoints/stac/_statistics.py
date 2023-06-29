import logging
from functools import cached_property
from typing import Any, NewType, Union

from geo_utils.vector import geojson_to_shapely, shapely_to_geojson_geometry
from joblib import Memory  # type: ignore
from numpy.typing import ArrayLike
from pyproj.crs import CRS
from requests import Response, get, post
from retry import retry

from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.scenes._utils import _validate_geometry
from pixels_utils.titiler import TITILER_ENDPOINT, get_assets_expression_query
from pixels_utils.titiler._utilities import validate_assets
from pixels_utils.titiler.endpoints.stac import Info
from pixels_utils.titiler.endpoints.stac._connect import online_status_stac
from pixels_utils.titiler.endpoints.stac._constants import STAC_ENDPOINT

STAC_statistics = NewType("STAC_statistics", Response)
STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"
STAC_STATISTICS_ENDPOINT = f"{STAC_ENDPOINT}/statistics"
QUERY_ASSETS = "assets"
QUERY_URL = "url"

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@memory.cache
@retry((RuntimeError, KeyError), tries=3, delay=2)
class Statistics:
    """
    Class to help faciilitate titiler STAC statistics endpoint.

    For more information, refer to [Titiler](https://developmentseed.org/titiler/endpoints/stac/#statistics) and
    [STAC](https://stacspec.org/en/about/stac-spec/).

    See a list of available assets for the EarthSearch collections in this Confluence page:
    https://sentera.atlassian.net/wiki/spaces/GML/pages/3357278209/EarthSearch+Collection+Availability

    Example:
        TODO: https://myendpoint/stac/statistics?url=https://somewhere.com/item.json&assets=B01

    Args:
        url (str): STAC item URL; the `https://somewhere.com/item.json` part of the example URL above.
        assets (Tuple[str], optional): Asset names; the `B01` part of the example URL above. Defaults to all available
        assets.

        titiler_endpoint (str): The `https://myendpoint` part of the example URL above. Defaults to
        `https://pixels.sentera.com/stac/info`.

        validate_individual_assets (bool): Whether to validate each asset individually during __init__(). Defaults to
        True.
    """

    def __init__(
        self,
        url: str,
        feature: Any = None,
        assets: ArrayLike[str] = None,
        expression: str = None,
        asset_as_band: bool = False,
        asset_bidx: ArrayLike[str] = None,
        coord_crs: CRS = CRS.from_epsg(4326),
        max_size: int = None,
        height: int = None,
        width: int = None,
        gsd: Union[int, float] = None,
        nodata: Union[str, int, float] = None,
        unscale: bool = False,
        resampling: str = "nearest",
        categorical: bool = False,
        c: ArrayLike[Union[float, int]] = None,
        p: ArrayLike[int] = None,
        histogram_bins: str = None,
        histogram_range: ArrayLike = None,
        clear_cache: bool = False,
        titiler_endpoint: str = TITILER_ENDPOINT,
        mask_scl: ArrayLike[SCL] = None,
        whitelist: bool = True,
        validate_individual_assets: bool = True,
    ):
        self.url = url
        self.feature = feature
        self.assets = assets
        self.expression = expression
        self.asset_as_band = asset_as_band
        self.asset_bidx = asset_bidx
        self.coord_crs = coord_crs
        self.max_size = max_size
        self.height = height
        self.width = width
        self.gsd = gsd
        self.nodata = nodata
        self.unscale = unscale
        self.resampling = resampling
        self.categorical = categorical
        self.c = c
        self.p = p
        self.histogram_bins = histogram_bins
        self.histogram_range = histogram_range
        self.clear_cache = clear_cache
        self.titiler_endpoint = titiler_endpoint
        self.mask_scl = mask_scl
        self.whitelist = whitelist
        # self.asset_metadata  # Runs cached_property on class declaration
        validate_assets(
            assets=self.assets,
            asset_names=self.asset_metadata.asset_names,
            validate_individual_assets=validate_individual_assets,
            url=self.url,
            stac_info_endpoint=STAC_INFO_ENDPOINT,
        )

        self._validate_args
        self.response  # Should run after asset_metadata to validate assets

    def _validate_args(self):
        _validate_geometry(self.feature)
        self.geometry = shapely_to_geojson_geometry(geojson_to_shapely(self.feature))
        self.scene_info = Info(
            url=self.url,
            assets=self.assets,
            titiler_endpoint=TITILER_ENDPOINT,
            validate_individual_assets=False,
        )
        if self.gsd and (self.height or self.width):
            logging.warning(
                'Both "gsd" and "height" or "width" were passed; "height" and "width" will be set based on "gsd".'
            )
            # TODO: Add height and width to get_assets_expression_query()
            self.height = None
            self.width = None
        self.df_nodata = self.scene_info.df_nodata  # Should issue a warning if "nodata" not available for collection

    @cached_property
    def response(
        self,
    ) -> STAC_statistics:
        """
        Return statistics on STAC item's COG.

        Returns:
            STAC_statistics: Response from the titiler stac statistics endpoint.
        """
        online_status_stac(self.titiler_endpoint, stac_endpoint=self.url)
        # self._validate_assets(
        #     validate_individual_assets=False
        # )  # Validate again in case anything changed since class declaration

        assert set(self.assets).issubset(
            set(self.scene_info.asset_metadata.asset_names)
        ), "Assets not valid for collection."
        query, _ = get_assets_expression_query(
            self.url,
            assets=self.assets,
            expression=self.expression,
            geojson=self.feature,
            mask_scl=self.mask_scl,
            whitelist=self.whitelist,
            nodata=self.nodata,
            gsd=self.gsd,
            resampling=self.resampling,
            categorical=self.categorical,
            c=self.c,
            p=self.p,
            histogram_bins=self.histogram_bins,
            histogram_range=self.histogram_range,
        )
        if self.clear_cache is True:
            headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        else:
            headers = {}

        if self.feature is None:
            logging.debug(
                'GET request to "%s" with the following args:\nparams: %s\nheaders: %s',
                STAC_STATISTICS_ENDPOINT,
                query,
                headers,
            )
            r = get(
                STAC_STATISTICS_ENDPOINT,
                params=query,
                headers=headers,
            )
        else:
            logging.debug(
                'POST request to "%s" with the following args:\nparams: %s\njson: %s\nheaders: %s',
                STAC_STATISTICS_ENDPOINT,
                query,
                self.feature,
                headers,
            )
            r = post(
                STAC_STATISTICS_ENDPOINT,
                params=query,
                json=self.feature,
                headers=headers,
            )

        if r.status_code != 200:
            logging.warning("Statistics %s request failed. Reason: %s", r.request.method, r.reason)
        return STAC_statistics(r)

import logging
import re
from dataclasses import field
from functools import cached_property
from typing import Any, ClassVar, List, NewType, Type, Union

from joblib import Memory  # type: ignore
from marshmallow import Schema, ValidationError, validate, validates, validates_schema
from marshmallow_dataclass import dataclass
from numpy.typing import ArrayLike
from pyproj.crs import CRS, CRSError
from rasterio.enums import Resampling
from requests import Response, get, post
from retry import retry

from pixels_utils.scenes._utils import _validate_geometry
from pixels_utils.titiler._constants import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import STAC_ENDPOINT, Info
from pixels_utils.titiler.endpoints.stac._connect import online_status_stac
from pixels_utils.titiler.endpoints.stac._utilities import to_pixel_dimensions

STAC_statistics = NewType("STAC_statistics", Response)
STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"
STAC_STATISTICS_ENDPOINT = f"{STAC_ENDPOINT}/statistics"
QUERY_ASSETS = "assets"
QUERY_URL = "url"

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@dataclass  # from marshmallow_dataclass
class QueryParamsStatistics:
    url: str
    feature: Any = None
    assets: List[str] = None
    expression: str = None
    # asset_as_band: bool = False
    asset_as_band: bool = None
    asset_bidx: List[str] = None
    coord_crs: str = CRS.from_epsg(4326).to_string()  # TODO: How to pass as a CRS type?
    max_size: int = None
    height: int = field(default=None, metadata=dict(validate=validate.Range(min=1)))
    width: int = field(default=None, metadata=dict(validate=validate.Range(min=1)))
    gsd: Union[int, float] = field(default=None, metadata=dict(validate=validate.Range(min=1e-6)))
    nodata: Union[int, float] = None
    # unscale: bool = False
    # resampling: str = "nearest"
    # categorical: bool = False
    unscale: bool = None
    resampling: str = field(default=None, metadata=dict(validate=validate.OneOf(list(Resampling._member_map_.keys()))))
    categorical: bool = None
    c: List[Union[float, int]] = None
    p: List[int] = None
    histogram_bins: str = None
    histogram_range: str = None
    Schema: ClassVar[Type[Schema]] = Schema

    @validates(field_name="coord_crs")
    def validate_coord_crs(self, coord_crs):
        if coord_crs is not None:
            auth_name, code = coord_crs.split(":")
            try:
                CRS.from_authority(auth_name=auth_name, code=code)
            except CRSError as e:
                raise ValidationError(e)
        else:
            raise ValidationError('"coord_crs" cannot be passed as `None`.')

    @validates(field_name="feature")
    def validate_geometry(self, feature):
        if feature is not None:
            try:
                _validate_geometry(feature)
            except TypeError as e:
                raise ValidationError(e)

    @validates_schema
    def validate_gsd_height_width(self, data, **kwargs):
        if data["gsd"] is not None and (data["height"] or data["width"]):
            raise ValidationError(
                'Both "gsd" and "height" or "width" were passed, but only "gsd" or "height" and "width" is allowed.',
            )

    @validates_schema
    def validate_assets_expression(self, data, **kwargs):
        if data["assets"] is None and data["expression"] is None:  # Neither are set
            raise ValidationError('Either "assets" or "expression" must be passed (both are null).')
        if data["assets"] is not None and data["expression"] is not None:  # Both are set
            raise ValidationError(
                'Both "assets" and "expression" were passed, but only one is allowed.',
            )
        if data["assets"] is not None and isinstance(data["assets"], str):
            raise ValidationError('"assets" must be a list of strings.')
            # TODO: How to set `data["assets"] = [data["assets"]] if isinstance(data["assets"], str) else data["assets"]``

    # class Meta:
    #     ordered = True  # maintains order in which fields were declared


class StatisticsPreValidation:
    def __init__(
        self,
        query_params: QueryParamsStatistics,
        titiler_endpoint: str = TITILER_ENDPOINT,
    ):
        self.query_params = query_params
        self.serialized_query_params = QueryParamsStatistics.Schema().dump(
            query_params
        )  # Use Schema(only=["url", "assets", "feature", "gsd"]) to filter

        self.titiler_endpoint = titiler_endpoint
        self.scene_info = None
        self.df_nodata = None

        errors = QueryParamsStatistics.Schema().validate(self.serialized_query_params)
        if errors:
            raise ValidationError(errors)

        # Step 1: Get valid assets for the URL (could also do after Step 3)
        self.scene_info = Info(
            url=self.serialized_query_params["url"],
            titiler_endpoint=TITILER_ENDPOINT,
            validate_individual_assets=True,
        )

        # Step 2: Extract the assets/expression from the query_params
        assets, expression = [self.serialized_query_params.get(i, None) for i in ["assets", "expression"]]
        self.serialized_query_params["assets"] = [assets] if isinstance(assets, str) else assets

        # Step 3: Get a list of assets from the assets or expression that was passed
        # regex retrieves assets from expression, delimites by comma, and drops empty strings, leftover digits, and
        # duplicates; e.g.:
        # list(set([i for i in re.sub("\W+", ",", "nir/red").split(",") if not i.isdigit()]))  # ['nir', 'red']
        # list(set([i for i in re.sub("\W+", ",", "3*(nir2/blue) + 0.13").split(",") if not i.isdigit()]))  # ['nir2', 'blue']
        # list(set([i for i in re.sub("\W+", ",", "3*(nir2/blue) + 0.13*nir2").split(",") if not i.isdigit()]))  # ['nir2', 'blue']

        assets_ = (
            list(
                set(
                    filter(
                        None, [i for i in re.sub("\W+", ",", expression).split(",") if not i.isdigit()]  # noqa: W605
                    )
                )
            )
            if expression
            else assets
        )

        # Step 4: Validate the list of assets against the available assets
        assert set(assets_).issubset(
            set(self.scene_info.assets_valid)
        ), f"The following assets are not available: {list(set(assets_) - set(self.scene_info.assets_valid))}"

        logging.info("StatisticsPreValidation passed: all required assets are available.")

        # TODO: Consider doing other checks/exposing other info in this class, e.g.:
        # self.df_nodata = (
        #     self.scene_info.df_nodata
        # )  # Should issue a warning if "nodata" not available for collection


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
    """

    def __init__(
        self,
        query_params: QueryParamsStatistics,
        clear_cache: bool = False,
        titiler_endpoint: str = TITILER_ENDPOINT,
        # mask_scl: Iterable[SCL] = None,
        mask_scl: ArrayLike = None,
        whitelist: bool = True,
    ):
        self.query_params = query_params
        self.serialized_query_params = QueryParamsStatistics.Schema().dump(
            query_params
        )  # Use Schema(only=["url", "assets", "feature", "gsd"]) to filter

        self.clear_cache = clear_cache
        self.titiler_endpoint = titiler_endpoint
        self.mask_scl = mask_scl
        self.whitelist = whitelist

        errors = QueryParamsStatistics.Schema().validate(self.serialized_query_params)
        if errors:
            raise ValidationError(errors)

        assets, expression = [self.serialized_query_params.get(i, None) for i in ["assets", "expression"]]
        self.serialized_query_params["assets"] = [assets] if isinstance(assets, str) else assets
        # asset_main = None if kwargs["assets"] is None else kwargs["assets"][0]

        feature, gsd, height, width = [
            self.serialized_query_params.get(i, None) for i in ["feature", "gsd", "height", "width"]
        ]
        self.serialized_query_params["height"], self.serialized_query_params["width"] = (
            to_pixel_dimensions(geojson=feature, height=height, width=width, gsd=gsd)
            if not [x for x in (feature, gsd) if x is None]  # if either feature or gsd is None
            else [None, None]
        )
        _ = self.serialized_query_params.pop("gsd", None)  # Delete gsd from serialized_query_params

        # self.geometry = shapely_to_geojson_geometry(geojson_to_shapely(self.query_params.feature))

        # TODO: if self.response is not a 200, issue a warning and notify user to validate assets prior to running stats

        self.response  # Should run at end of __post_init__() after validate_assets()

    @cached_property
    def response(
        self,
    ) -> STAC_statistics:
        """
        Return statistics on STAC item's COG.

        Returns:
            STAC_statistics: Response from the titiler stac statistics endpoint.
        """
        online_status_stac(self.titiler_endpoint, stac_endpoint=self.query_params.url)
        # query = generate_base_query(**self.serialized_query_params)
        query = {k: v for k, v in self.serialized_query_params.items() if v is not None}
        # TODO: Consider mask_scl and whitelist, adjusting assets and/or expression accordingly
        if self.clear_cache is True:
            headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        else:
            headers = {}

        if self.query_params.feature is None:
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
                self.query_params.feature,
                headers,
            )
            r = post(
                STAC_STATISTICS_ENDPOINT,
                params=query,
                json=self.query_params.feature,
                headers=headers,
            )

        if r.status_code != 200:
            logging.warning("Statistics %s request failed. Reason: %s", r.request.method, r.reason)
        return STAC_statistics(r)

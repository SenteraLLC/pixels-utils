import logging
import re
from dataclasses import field
from enum import Enum
from functools import cached_property
from typing import Any, ClassVar, List, Type, Union

from joblib import Memory  # type: ignore
from marshmallow import Schema, ValidationError, validate, validates, validates_schema
from marshmallow_dataclass import dataclass
from pyproj.crs import CRS, CRSError
from rasterio.enums import Resampling
from requests import get, post
from retry import retry

from pixels_utils.scenes._utils import _validate_geometry
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints import STAC_ENDPOINT
from pixels_utils.titiler.endpoints.stac import Info
from pixels_utils.titiler.endpoints.stac._connect import online_status_stac
from pixels_utils.titiler.endpoints.stac._utilities import to_pixel_dimensions
from pixels_utils.titiler.endpoints.stac.types import STAC_statistics
from pixels_utils.titiler.mask._mask import build_numexpr_mask_enum

STAC_INFO_ENDPOINT = f"{STAC_ENDPOINT}/info"
STAC_STATISTICS_ENDPOINT = f"{STAC_ENDPOINT}/statistics"

memory = Memory("/tmp/pixels-utils-cache/", bytes_limit=2**30, verbose=0)
memory.reduce_size()  # Pre-emptively reduce the cache on start-up (must be done manually)


@dataclass  # from marshmallow_dataclass
class QueryParamsStatistics:
    """Organize and validate QueryParams for the STAC statistics endpoint."""

    url: str
    feature: Any = None
    assets: List[str] = None
    expression: str = None
    asset_as_band: bool = None
    asset_bidx: List[str] = None
    coord_crs: str = None
    max_size: int = None
    height: int = field(default=None, metadata=dict(validate=validate.Range(min=1)))
    width: int = field(default=None, metadata=dict(validate=validate.Range(min=1)))
    gsd: Union[int, float] = field(default=None, metadata=dict(validate=validate.Range(min=1e-6)))
    nodata: Union[int, float] = None
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

    @validates(field_name="feature")
    def validate_geometry(self, feature):
        if feature is not None:
            try:
                _validate_geometry(feature)
            except TypeError as e:
                raise ValidationError(e)

    @validates(field_name="asset_as_band")
    def validate_asset_as_band(self, asset_as_band):
        if asset_as_band is None or asset_as_band is False:
            logging.warning(
                (
                    "If you don't use `asset_as_band=True` option, band indexes must be passed within the expression "
                    '(e.g., "(nir_b1/red_b1)") - this is a primary reason for "Bad Request" errors.'
                )
            )

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
        """
        Performs pre-validation of Statistics QueryParams, which should run before making many calls via `Statistics`.

        Args:
            query_params (QueryParamsStatistics): The query parameters to validate.
            titiler_endpoint (str, optional): The titiler endpoint to perform requests. Defaults to TITILER_ENDPOINT.

        Raises:
            ValidationError: If the query_params are invalid (i.e., if they do not properly serialize).
            AssertionError: If any of the assets (or assets within the expression) are not available for the collection.
        """
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

        # Step 1: Extract the assets/expression from the query_params
        assets, expression = [self.serialized_query_params.get(i, None) for i in ["assets", "expression"]]
        self.serialized_query_params["assets"] = [assets] if isinstance(assets, str) else assets

        # Step 2: Get a list of assets from the assets or expression that was passed
        # regex retrieves assets from expression, delimites by comma, and drops empty strings, leftover digits, and
        # duplicates; e.g.:
        # list(set([i for i in re.sub("\W+", ",", "nir/red").split(",") if not i.isdigit()]))  # ['nir', 'red']
        # list(set([i for i in re.sub("\W+", ",", "3*(nir2/blue) + 0.13").split(",") if not i.isdigit()]))  # ['nir2', 'blue']
        # list(set([i for i in re.sub("\W+", ",", "3*(nir2/blue) + 0.13*nir2").split(",") if not i.isdigit()]))  # ['nir2', 'blue']

        assets_ = (
            list(
                set(
                    filter(
                        None, [i for i in re.sub(r"\W+", ",", expression).split(",") if not i.isdigit()]  # noqa: W605
                    )
                )
            )
            if expression
            else assets
        )

        # Step 3: Get valid assets for the URL, passing assets_ from Step 2 above
        self.scene_info = Info(
            url=self.serialized_query_params["url"],
            assets=assets_,
            titiler_endpoint=TITILER_ENDPOINT,
            check_individual_asset_availability=True,
        )

        # Step 4: Validate the list of assets against the available assets
        if set(assets_).issubset(set(self.scene_info.assets_valid)):
            logging.info("StatisticsPreValidation PASSED. All required assets are available.")
        else:
            raise ValidationError(
                "StatisticsPreValidation FAILED. The following assets are not available: "
                f"{list(set(assets_) - set(self.scene_info.assets_valid))}"
            )

        # TODO: Consider doing other checks/exposing other info in this class, e.g.:
        # self.df_nodata = (
        #     self.scene_info.df_nodata
        # )  # Should issue a warning if "nodata" not available for collection


@retry((RuntimeError, KeyError), tries=3, delay=2)
class Statistics:
    """
    Class to help faciilitate titiler STAC statistics endpoint.

    For more information, refer to [Titiler](https://developmentseed.org/titiler/endpoints/stac/#statistics) and
    [STAC](https://stacspec.org/en/about/stac-spec/).

    See a list of available assets for the EarthSearch collections in this Confluence page:
    https://sentera.atlassian.net/wiki/spaces/GML/pages/3357278209/EarthSearch+Collection+Availability

    Example:
        https://pixels.sentera.com/stac/statistics?&assets=nir&feature=type&feature=geometry&feature=properties&url=https%3A%2F%2Fearth-search.aws.element84.com%2Fv1%2Fcollections%2Fsentinel-2-l2a%2Fitems%2FS2B_10TGS_20220608_0_L2A
        https://pixels.sentera.com/stac/statistics?asset_as_band=True&expression=%28nir-red%29%2F%28nir%2Bred%29&feature=type&feature=geometry&feature=properties&url=https%3A%2F%2Fearth-search.aws.element84.com%2Fv1%2Fcollections%2Fsentinel-2-l2a%2Fitems%2FS2B_10TGS_20220608_0_L2A

    Args:
        query_params (QueryParamsStatistics): The QueryParams to pass to the statistics endpoint (see titiler docs for
        more information).
        clear_cache (bool, optional): Whether to clear the cache. Defaults to False.
        titiler_endpoint (str): The `https://myendpoint` part of the example URL above. Defaults to
        `https://pixels.sentera.com/stac/statistics`.
    """

    def __init__(
        self,
        query_params: QueryParamsStatistics,
        clear_cache: bool = False,
        titiler_endpoint: str = TITILER_ENDPOINT,
        mask_enum: List[Enum] = None,
        mask_asset: str = None,
        whitelist: bool = True,
    ):
        self.query_params = query_params
        self.serialized_query_params = QueryParamsStatistics.Schema().dump(
            query_params
        )  # Use Schema(only=["url", "assets", "feature", "gsd"]) to filter

        self.clear_cache = clear_cache
        self.titiler_endpoint = titiler_endpoint
        self.mask_enum = mask_enum
        self.mask_asset = mask_asset
        self.whitelist = whitelist

        errors = QueryParamsStatistics.Schema().validate(self.serialized_query_params)
        if errors:
            raise ValidationError(errors)

        assets, expression = [self.serialized_query_params.get(i, None) for i in ["assets", "expression"]]
        self.serialized_query_params["assets"] = [assets] if isinstance(assets, str) else assets

        feature, gsd, height, width = [
            self.serialized_query_params.get(i, None) for i in ["feature", "gsd", "height", "width"]
        ]
        # Run to_pixel_dimensions() if feature is set (otherwise pass whatever already exists for height and width
        self.serialized_query_params["height"], self.serialized_query_params["width"] = (
            to_pixel_dimensions(geojson=feature, height=height, width=width, gsd=gsd)
            if feature is not None
            else [height, width]
        )
        _ = self.serialized_query_params.pop("gsd", None)  # Delete gsd from serialized_query_params
        self.serialized_query_params["coord-crs"] = self.serialized_query_params.pop(
            "coord_crs", None
        )  # titiler anomaly

        # Note: Assets do not do not accept numexpr functions
        if self.mask_enum is not None and self.serialized_query_params["assets"] is not None:
            logging.warning(
                "`assets` do not accept numexpr functions, so `mask_enum` will be ignored. Use `expression` instead."
            )
        if self.mask_enum is not None and self.serialized_query_params["expression"] is not None:
            logging.debug("Adding masking parameters to `expression`.")
            self.serialized_query_params["expression"] = build_numexpr_mask_enum(
                expression=self.serialized_query_params["expression"],
                mask_enum=self.mask_enum,
                whitelist=self.whitelist,
                mask_value=self.serialized_query_params["nodata"],
                mask_asset=self.mask_asset,
            )
            self.serialized_query_params["nodata"] = (
                0.0 if self.serialized_query_params["nodata"] is None else self.serialized_query_params["nodata"]
            )
        # self.geometry = shapely_to_geojson_geometry(geojson_to_shapely(self.query_params.feature))
        self.response

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
        query = {k: v for k, v in self.serialized_query_params.items() if v is not None}

        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"} if self.clear_cache is True else {}

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

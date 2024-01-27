from enum import Enum, auto
from functools import cached_property

from spyndex import indices as spyndex_indices

from pixels_utils.stac_catalogs._expression_helper import Expression, Expressions
from pixels_utils.stac_catalogs.earthsearch import AutoDashNameEnum
from pixels_utils.stac_metadata import STACMetaData

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

    @cached_property
    def _version(self):
        return "v1"


def _generate_experession_override(expression: str, assets: list[str], assets_override: list[str]) -> str:
    """Return expression_override with assets replaced by assets_override."""
    expression_override = expression
    for asset_common, asset_collection in zip(assets, assets_override):
        expression_override = expression_override.replace(asset_common, asset_collection)
    return expression_override


def expression_from_collection(
    collection: EarthSearchCollections = EarthSearchCollections.sentinel_2_l2a, spectral_index: str = "NDVI"
) -> Expression:
    """
    Returns an Expression object for a given collection and spectral index.

    See `spyndex_indices` for a list of available spectral indices.

    Args:
        collection (EarthSearchCollections, optional): The collection that spectral_index should be tailored to.
        Defaults to EarthSearchCollections.sentinel_2_l2a.

        spectral_index (str, optional): The acronym for the spectral index you'd like returned as an Expression. Must be
        a spectral index available via spyndex. Defaults to "NDVI".

    Returns:
        Expression: The tailored Expression object.
    """
    if spectral_index not in spyndex_indices.keys():
        raise AssertionError(f"{spectral_index} is not a valid spectral index (must be available via spyndex.indices).")
    if collection._version != "v1":
        raise AssertionError(
            f"The `collection` and `expression_from_collection()` function versions do not match ({collection._version} vs "
            f'v1). Ensure both the "{collection}" and expression_from_collection() function are imported from the same '
            "version of `pixels_utils.stac_catalogs.earthsearch`."
        )
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    # TODO: stac_metadata.parse_asset_bands("eo:bands", return_dataframe=True) for support of EarthSearch v0

    # get list of `name` values where `common_name` matches spectral_index
    assets_ = Expression(spyndex_object=spyndex_indices[spectral_index]).assets
    expression_str_ = Expression(spyndex_object=spyndex_indices[spectral_index]).expression

    df_collection_assets = stac_metadata.parse_asset_bands("eo:bands", return_dataframe=True)
    df_expr_assets_ = df_collection_assets[df_collection_assets["common_name"].isin(assets_)][
        ["name", "common_name"]
    ].drop_duplicates(subset="common_name")

    # Check if all `common_names` match `names` (i.e., collection_names)
    if any([row["name"] != row["common_name"] for _, row in df_expr_assets_.iterrows()]):
        # Raise error if collection does not have assets available
        for asset in assets_:
            if asset not in df_expr_assets_["common_name"].values:
                raise ValueError(
                    f'"{asset}" is required for spectral index "{spectral_index}", but is not a valid asset (i.e., '
                    f'"common_name") in collection "{collection}".\nValid "common_names":\n'
                    f'{df_collection_assets["common_name"].values}'
                )
        # Set assets_override and expression_override based on available `name` values for the collection.
        assets_override = [
            df_expr_assets_[df_expr_assets_["common_name"] == asset]["name"].values[0] for asset in assets_
        ]
        expression_override = _generate_experession_override(expression_str_, assets_, assets_override)
    else:
        assets_override, expression_override = None, None

    expression = Expression(
        spyndex_object=spyndex_indices[spectral_index],
        assets_override=assets_override,
        expression_override=expression_override,
    )

    if not set(expression.assets).issubset(set(stac_metadata.asset_names)):
        raise AssertionError(
            f'Assets for spectral index "{spectral_index}" are not available in collection "{collection}".'
        )
    return expression


def expressions_from_collection(
    collection: EarthSearchCollections = EarthSearchCollections.sentinel_2_l2a,
) -> Expressions:
    """
    Returns an Expressions object for a given collection containing all available spectral indices.

    Args:
        collection (EarthSearchCollections, optional): The collection to generate Expressions for. Defaults to
        EarthSearchCollections.sentinel_2_l2a.

    Returns:
        Expressions: The Expressions object containing all available spectral indices for the given collection.
    """
    if collection._version != "v1":
        raise AssertionError(
            f"The `collection` and `expression_from_collection()` function versions do not match ({collection._version} vs "
            f'v1). Ensure both the "{collection}" and expression_from_collection() function are imported from the same '
            "version of `pixels_utils.stac_catalogs.earthsearch`."
        )
    # Get list of assets in collection and filter spyndex_bands by collection assets
    stac_collection_url = EARTHSEARCH_COLLECTION_URL.format(collection=collection.name)
    stac_metadata = STACMetaData(collection_url=stac_collection_url)
    return Expressions(
        **{
            spectral_index: (
                Expression(spyndex_object=spyndex_indices[spectral_index])
                if set(Expression(spyndex_object=spyndex_indices[spectral_index]).assets).issubset(
                    set(stac_metadata.asset_names)
                )
                else None
            )
            for spectral_index in spyndex_indices
        }
    )

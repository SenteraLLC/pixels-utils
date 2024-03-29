from enum import Enum
from typing import Generator, List, Union


def _build_mask_by_assignment(
    assignment: Generator[Union[int, Enum], Union[int, float], None], else_value: Union[int, float], mask_asset: str
) -> str:
    """Builds the NumExpr where clause to mask asset by scene classification.

    Args:
        assignment (Generator[Union[int, Enum], Union[int, float]]): The assignment to be built into a NumExpr where
        clause. The assignment is a generator of tuples, where the first element represents the value of pixels to
        replace, and the second element represents the value to replace them with.

        else_value (Union[int, float]): The value to assign to pixels that do not match.
        mask_asset (str): The asset to be masked.

    Whitelist example:
        >>> from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, expression_from_collection
        >>> from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL, Sentinel2_SCL_Group

        >>> EXPRESSION_NDVI = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI").expression
        >>> nodata = 0
        >>> assignment = ((class_enum, EXPRESSION_NDVI) for class_enum in Sentinel2_SCL_Group.ARABLE)
        >>> print(_build_mask_by_assignment(assignment=assignment, else_value=nodata, mask_asset="scl"))
        "where(scl==4,(nir-red)/(nir+red),where(scl==5,(nir-red)/(nir+red),0))"

    Blacklist example:
        >>> EXPRESSION_NDVI = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI").expression
        >>> assignment = ((class_enum, nodata) for class_enum in Sentinel2_SCL_Group.ARABLE)
        >>> print(_build_mask_by_assignment(assignment=assignment, else_value=EXPRESSION_NDVI, mask_asset="scl"))
        "where(scl==2,0,where(scl==3,0,where(scl==8,0,where(scl==9,0,where(scl==10,0,(nir-red)/(nir+red))))))"
    """
    class_enum, expression = next(assignment)
    try:
        else_value_final = _build_mask_by_assignment(
            assignment=assignment, else_value=else_value, mask_asset=mask_asset
        )
    except StopIteration:
        else_value_final = else_value
    return f"where({mask_asset}=={int(class_enum)},{expression},{else_value_final})"


def build_numexpr_mask_enum(
    expression: str,
    mask_enum: List[Enum],
    mask_asset: str = "scl",
    whitelist: bool = True,
    mask_value: Union[int, float] = 0.0,
) -> str:
    """Builds the NumExpr `expression` as a "where clause" to mask `mask_enum` values from STAC Asset(s).

    Note:
        Multiple expressions must be semicolon (;) delimited (e.g., "b1/b2;b2+b3").
        Refer to the [titiler source code](https://github.com/developmentseed/titiler/blob/495531cc81d7fb4e06299f6bd390d19048533373/src/titiler/core/titiler/core/dependencies.py#L122-L124)
        for more information.

    Args:
        expression (str): The expression to be built into a NumExpr where clause.
        mask_enum (List[Enum]): The list of pixel values to be masked out.
        mask_asset (str, optional): The asset to be masked. Defaults to "scl".
        whitelist (bool, optional): Whether scene classifications are built via a whitelist or blacklist.
        `whitelist=True` indicates that all pixels that match the `mask_enum` values will be kept, whereas
        `whitelist=False` indicates that all pixels that match the `mask_enum` values will be masked out.

        mask_value (Union[int, float], optional): The mask value; will be used to represent all pixels masked based on
        the passed `mask_enum` and `whitelist` combination. Defaults to 0.0.

    Returns:
        str: The NumExpr "where clause" to mask `mask_enum` values from STAC Asset(s).
    """
    mask_value = 0.0 if mask_value is None else mask_value

    expression = [expression] if isinstance(expression, str) else expression
    if whitelist is True:  # whitelist - {expr} is part of the assignment
        #
        assignment = ((class_enum, "{expr}") for class_enum in mask_enum)
        numexpr_str_template = "{0};".format(
            _build_mask_by_assignment(assignment, else_value=mask_value, mask_asset="{mask_asset}")
        )
    else:  # blacklist - {expr} is the `else_value`
        assignment = ((class_enum, mask_value) for class_enum in mask_enum)
        numexpr_str_template = "{0};".format(
            _build_mask_by_assignment(assignment, else_value="{expr}", mask_asset="{mask_asset}")
        )
    return "".join([numexpr_str_template.format(expr=expr, mask_asset=mask_asset) for expr in expression])

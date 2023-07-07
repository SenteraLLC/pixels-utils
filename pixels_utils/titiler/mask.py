import logging
from enum import Enum
from typing import Generator, List, Union

from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics


def validate_mask_enum(
    query_params: QueryParamsStatistics,
    mask_enum: List[Enum],
) -> bool:
    """
    Validates that `query_params` and `mask_enum` are valid to be used .

    """
    assert mask_enum is not None, "`mask_enum` must be passed to validate_mask_enum()."
    assets, expression = query_params.assets, query_params.expression
    if assets is not None:
        logging.warning(
            "`assets` do not accept numexpr functions, so `mask_enum` will be ignored. Use `expression` instead."
        )
        return False
    if expression is not None:
        logging.info("Adding masking parameters to `expression`.")
        return True
    return False


def _build_mask_by_assignment(
    assignment: Generator[Union[int, Enum], Union[int, float], None], else_value: Union[int, float]
) -> str:
    """Builds the NumExpr where clause to mask by scene classification.

    Args:
        assignment (Generator[Union[int, Enum], Union[int, float]]): The assignment to be built into a NumExpr where
        clause. The assignment is a generator of tuples, where the first element represents the value of pixels to
        replace, and the second element represents the value to replace them with.

        else_value (Union[int, float]): The value to assign to pixels that do not match.

    Whitelist example:
        >>> from pixels_utils.constants.sentinel2 import EXPRESSION_NDVI, SCL_GROUP_ARABLE
        >>> nodata = 0
        >>> scl_and_exp = ((scl, EXPRESSION_NDVI) for scl in SCL_GROUP_ARABLE)
        >>> print(_build_mask_by_assignment(assignment=scl_and_exp, else_value=nodata))
        "where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0))"

    Blacklist example:
        >>> from pixels_utils.constants.sentinel2 import SCL_GROUP_CLOUDS
        >>> scl_and_exp_bl = ((scl, nodata) for scl in SCL_GROUP_CLOUDS)
        >>> print(_build_mask_by_assignment(assignment=iter(scl_and_exp_bl), else_value=EXPRESSION_NDVI))
        "where(SCL == 2, 0, where(SCL == 3, 0, where(SCL == 8, 0, where(SCL == 9, 0, where(SCL == 10, 0, (B08-B04)/(B08+B04))))))"
    """
    scl, assignment = next(assignment)
    try:
        else_value_final = _build_mask_by_assignment(assignment=assignment, else_value=else_value)
    except (StopIteration, TypeError):
        else_value_final = else_value
    return f"where(SCL=={int(scl)},{assignment},{else_value_final})"


def build_numexpr_mask_enum(
    expression: str,
    mask_enum: List[Enum],
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
    if whitelist is True:
        assignment = ((scl, "{expr}") for scl in mask_enum)
        numexpr_str_template = "{0};".format(_build_mask_by_assignment(assignment, else_value=mask_value))
    else:  # blacklist
        assignment = ((scl, mask_value) for scl in mask_enum)
        numexpr_str_template = "{0};".format(_build_mask_by_assignment(assignment, else_value="{asset}"))
    return "".join([numexpr_str_template.format(expr=expr) for expr in expression])

from typing import Iterable, Union

from pixels_utils.constants.sentinel2 import SCL


def _build_mask_by_assignment(scl_assignment, else_value):
    """Builds the NumExpr where clause to mask by scene classification.

    Whitelist example:
        >>> from pixels_utils.constants.sentinel2 import EXPRESSION_NDVI, SCL_GROUP_ARABLE
        >>> nodata = 0
        >>> scl_and_exp = ((scl, EXPRESSION_NDVI) for scl in SCL_GROUP_ARABLE)
        >>> print(_build_mask_by_assignment(scl_and_exp, nodata))
        "where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0))"

    Blacklist example:
        >>> from pixels_utils.constants.sentinel2 import SCL_GROUP_CLOUDS
        >>> scl_and_exp_bl = ((scl, nodata) for scl in SCL_GROUP_CLOUDS)
        >>> print(_build_mask_by_assignment(iter(scl_and_exp_bl), EXPRESSION_NDVI))
        "where(SCL == 2, 0, where(SCL == 3, 0, where(SCL == 8, 0, where(SCL == 9, 0, where(SCL == 10, 0, (B08-B04)/(B08+B04))))))"
    """
    scl, assignment = next(scl_assignment)
    try:
        else_value_final = _build_mask_by_assignment(scl_assignment, else_value)
    except StopIteration:
        else_value_final = else_value
    return f"where(SCL == {int(scl)}, {assignment}, {else_value_final})"


def build_numexpr_scl_mask(
    assets: Iterable[str] = None,
    expression: str = None,
    mask_scl: Iterable[SCL] = None,
    whitelist: bool = True,
    mask_value: Union[int, float] = 0.0,
) -> str:
    """Builds the NumExpr where clause based on assets/expression and SCL list.

    Args:
        assets ():
        expression ():
        mask_scl ():
        whitelist (bool, optional): Whether scene classifications are built via a
        whitelist or blacklist. `whitelist` indicates that all pixels that match the
        SCL in `scl_and_outcome` will be kept, whereas `blacklist` indicates that all
        pixels that match the SCL in `scl_and_outcome` will be masked out.
        mask_value (str, optional): The mask value; will be used to represent all pixels
        masked by <mask_scl>/<whitelist> combination. Defaults to 0.0.

    Returns:
        str: _description_
    """
    mask_value = 0.0 if mask_value is None else mask_value
    if assets is not None and mask_scl is not None:
        assets = [assets] if isinstance(assets, str) else assets
        if whitelist is True:
            scl_assignment = ((scl, "{asset}") for scl in mask_scl)
            numexpr_str_template = "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value=mask_value)
            )
        else:  # blacklist
            scl_assignment = ((scl, mask_value) for scl in mask_scl)
            numexpr_str_template = "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value="{asset}")
            )
        return [numexpr_str_template.format(asset=asset) for asset in assets]
    elif assets is not None and mask_scl is None:
        return assets

    if expression is not None and mask_scl is not None:
        if whitelist is True:
            scl_assignment = ((scl, expression) for scl in mask_scl)
            return "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value=mask_value)
            )
        else:
            scl_assignment = ((scl, mask_value) for scl in mask_scl)
            return "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value=expression)
            )
    elif expression is not None and mask_scl is None:
        return expression

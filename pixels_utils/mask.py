from typing import Iterable, Union

from pixels_utils.constants.sentinel2 import SCL, SCL_GROUP_ARABLE


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
    mask_scl: Iterable[SCL] = SCL_GROUP_ARABLE,
    whitelist: bool = True,
    nodata: Union[int, float] = 0,
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
        nodata (str, optional): The nodata value; will be used to ignore all pixels
        whose classification is not included in <scl_and_outcome>. Defaults to
        `str(SCL.NO_DATA)`.

    Returns:
        str: _description_
    """
    nodata = 0.0 if nodata is None else nodata
    if assets is not None and mask_scl is not None:
        raise NotImplementedError(
            "<assets> not yet implemented for clouds.build_numexpr_scl_mask()"
        )  # TODO
        if whitelist is True:
            pass
        else:
            pass
    elif assets is not None and mask_scl is None:
        return assets

    if expression is not None and mask_scl is not None:
        if whitelist is True:
            scl_assignment = ((scl, expression) for scl in mask_scl)
            return "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value=nodata)
            )
        else:  # blacklist
            scl_assignment = ((scl, nodata) for scl in mask_scl)
            return "{0};".format(
                _build_mask_by_assignment(scl_assignment, else_value=expression)
            )
    elif expression is not None and mask_scl is None:
        return expression

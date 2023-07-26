from typing import Dict, Iterable

from numpy import count_nonzero as np_count_nonzero
from numpy import isin as np_isin
from numpy.ma import count as npma_count
from numpy.ma import count_masked as npma_count_masked
from numpy.typing import ArrayLike

from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL

# A_: Total within and total outside feature
A1 = "feature_in_pix"
A2 = "feature_out_pix"
A3 = "feature_in_pct"
A4 = "feature_out_pct"
# B_: Total unmasked (valid) and masked (invalid) within feature
B1 = "whitelist_pix"
B2 = "blacklist_pix"
B3 = "whitelist_pct"
B4 = "blacklist_pct"
# C_: Breakdown of class within feature
C1 = "pix_by_class"
C2 = "pct_by_class"


def count_feature_pixels(data: ArrayLike, band_names: Iterable) -> Dict:
    """
    Counts valid and invalid pixels for each band in data array.

    Args:
        data (ArrayLike): Data array. Must be 3-dimensional.
        band_names (Iterable): Band names. These will be the keys of the returned dict.

    Returns:
        Dict: Geojson pixel stats within and outside feature.
    """
    feature_stats = {}
    feature_stats[A1] = {band_name: npma_count(data[i, :, :]) for i, band_name in enumerate(band_names)}
    feature_stats[A2] = {band_name: npma_count_masked(data[i, :, :]) for i, band_name in enumerate(band_names)}
    # feature_stats["valid_pix"] = {band_name: count(data[i, :, :]) - count_masked(data[i, :, :]) for i, band_name in enumerate(band_names)}
    feature_stats[A3] = {
        bn1: v_pix / (v_pix + iv_pix) * 100
        for (bn1, v_pix), (_, iv_pix) in zip(feature_stats[A1].items(), feature_stats[A2].items())
    }
    feature_stats[A4] = {
        bn1: iv_pix / (v_pix + iv_pix) * 100
        for (bn1, v_pix), (_, iv_pix) in zip(feature_stats[A1].items(), feature_stats[A2].items())
    }
    return feature_stats


def count_valid_whitelist_pixels(array_classes: ArrayLike, mask_enum: Iterable, whitelist: bool) -> Dict:
    """
    Counts valid and invalid pixels in Sentinel2_SCL array.

    Args:
        array_classes (ArrayLike): Class array (e.g., Sentinel2 SCL classes). Must be 3-dimensional.
        mask_enum (Iterable): Sentinel-2 SCL classes to consider for pixel-based masking. If `None`,
        pixel-based masking is not implemented. The `whitelist` setting must be considered to determine if `mask_enum`
        classes are deemed to be valid or invalid.

        whitelist (bool): If `True`, the passed `mask_enum` classes are considerd "valid" for pixel-based
        masking; if `False`, the passed `mask_enum` classes are considered "invalid" for pixel-based masking.

    Returns:
        Dict: Mask ENUM pixel stats A) within and outside feature, B) unmasked (valid) and masked (invalid) within feature,
        and breakdown of Mask ENUM classes within feature.
    """
    mask_enum_stats = {}

    # A_: Total within and total outside feature
    mask_enum_stats[A1] = npma_count(array_classes[0, :, :])  # Intersects feature
    mask_enum_stats[A2] = npma_count_masked(array_classes[0, :, :])  # Outside feature
    mask_enum_stats[A3] = mask_enum_stats[A1] / (mask_enum_stats[A1] + mask_enum_stats[A2]) * 100
    mask_enum_stats[A4] = mask_enum_stats[A2] / (mask_enum_stats[A1] + mask_enum_stats[A2]) * 100

    # B_: Total unmasked (valid) and masked (invalid) within feature
    if mask_enum and whitelist:
        scl_wl = mask_enum
    elif mask_enum and whitelist is False:
        scl_wl = set(Sentinel2_SCL) - set(mask_enum)
    else:
        scl_wl = None
        mask_enum_stats[B1] = None
        mask_enum_stats[B2] = None
        mask_enum_stats[B3] = None
        mask_enum_stats[B4] = None

    if scl_wl:
        mask_enum_stats[B1] = np_count_nonzero(
            np_isin(array_classes.data[0, :, :], scl_wl)
        )  # count of pixels in scl_wl (not including feature mask)
        mask_enum_stats[B2] = (
            mask_enum_stats[A1] - mask_enum_stats[B1]
        )  # count of pixels NOT in scl_wl (not including feature mask)
        # invalid_mask_enum_pix + valid_mask_enum_pix  # should equal sum(list(mask_enum_stats[C1].values())) - mask_enum_stats[C1]["GEOJSON_MASK"]
        mask_enum_stats[B3] = mask_enum_stats[B1] / (mask_enum_stats[B1] + mask_enum_stats[B2]) * 100
        mask_enum_stats[B4] = mask_enum_stats[B2] / (mask_enum_stats[B1] + mask_enum_stats[B2]) * 100

    # C_: Breakdown of Mask ENUM classes within feature
    mask_enum_stats[C1] = {scl.name: np_count_nonzero(array_classes.data[0, :, :] == scl) for scl in Sentinel2_SCL}
    mask_enum_stats[C2] = {
        scl.name: (np_count_nonzero(array_classes.data[0, :, :] == scl) / mask_enum_stats[A1]) * 100
        for scl in Sentinel2_SCL
    }
    mask_enum_stats[C1]["NO_DATA"] = mask_enum_stats[C1]["NO_DATA"] - mask_enum_stats[A2]
    mask_enum_stats[C2]["NO_DATA"] = (mask_enum_stats[C1]["NO_DATA"] / mask_enum_stats[A1]) * 100
    return mask_enum_stats

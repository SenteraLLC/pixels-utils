import logging
from typing import Dict, Iterable, Tuple, Union

import numpy.ma as ma
from numpy import count_nonzero as np_count_nonzero
from numpy import expand_dims as np_expand_dims
from numpy import isin as np_isin
from numpy import logical_not as np_logical_not
from numpy import min_scalar_type as np_min_scalar_type
from numpy import ndarray as np_ndarray
from numpy import repeat as np_repeat
from numpy import zeros_like
from numpy.ma import count as npma_count
from numpy.ma import count_masked as npma_count_masked
from numpy.typing import ArrayLike, DTypeLike

from pixels_utils.constants.decorators import requires_rasterio
from pixels_utils.constants.sentinel2 import SCL
from pixels_utils.constants.types import STAC_crop

try:
    from rasterio import Env
    from rasterio.io import DatasetReader, MemoryFile
    from rasterio.profiles import Profile

    from pixels_utils.rasterio_helper import ensure_data_profile_consistency, save_image
except ImportError:
    logging.exception("Optional dependency <rasterio> not imported. Some features are not available.")


# A_: Total within and total outside geojson
A1 = "geojson_in_pix"
A2 = "geojson_out_pix"
A3 = "geojson_in_pct"
A4 = "geojson_out_pct"
# B_: Total unmasked (valid) and masked (invalid) within geojson
B1 = "whitelist_pix"
B2 = "blacklist_pix"
B3 = "whitelist_pct"
B4 = "blacklist_pct"
# C_: Breakdown of SCL classes within geojson
C1 = "pix_by_scl"
C2 = "pct_by_scl"


def count_geojson_pixels(data: ArrayLike, band_names: Iterable) -> Dict:
    """
    Counts valid and invalid pixels for each band in data array.

    Args:
        data (ArrayLike): Data array. Must be 3-dimensional.
        band_names (Iterable): Band names. These will be the keys of the returned dict.

    Returns:
        Dict: Geojson pixel stats within and outside geojson.
    """
    geojson_stats = {}
    geojson_stats[A1] = {band_name: npma_count(data[i, :, :]) for i, band_name in enumerate(band_names)}
    geojson_stats[A2] = {band_name: npma_count_masked(data[i, :, :]) for i, band_name in enumerate(band_names)}
    # geojson_stats["valid_pix"] = {band_name: count(data[i, :, :]) - count_masked(data[i, :, :]) for i, band_name in enumerate(band_names)}
    geojson_stats[A3] = {
        bn1: v_pix / (v_pix + iv_pix) * 100
        for (bn1, v_pix), (_, iv_pix) in zip(geojson_stats[A1].items(), geojson_stats[A2].items())
    }
    geojson_stats[A4] = {
        bn1: iv_pix / (v_pix + iv_pix) * 100
        for (bn1, v_pix), (_, iv_pix) in zip(geojson_stats[A1].items(), geojson_stats[A2].items())
    }
    return geojson_stats


def count_valid_whitelist_pixels(data_scl: ArrayLike, mask_scl: Iterable, whitelist: bool) -> Dict:
    """
    Counts valid and invalid pixels in SCL array.

    Args:
        data_scl (ArrayLike): SCL array. Must be 3-dimensional.
        mask_scl (Iterable): Sentinel-2 SCL classes to consider for pixel-based masking. If `None`,
        pixel-based masking is not implemented. The `whitelist` setting must be considered to determine if `mask_scl`
        classes are deemed to be valid or invalid.

        whitelist (bool): If `True`, the passed `mask_scl` classes are considerd "valid" for pixel-based
        masking; if `False`, the passed `mask_scl` classes are considered "invalid" for pixel-based masking.

    Returns:
        Dict: SCL pixel stats A) within and outside geojson, B) unmasked (valid) and masked (invalid) within geojson,
        and breakdown of SCL classes within geojson.
    """
    mask_scl_stats = {}

    # A_: Total within and total outside geojson
    mask_scl_stats[A1] = npma_count(data_scl[0, :, :])  # Intersects geojson
    mask_scl_stats[A2] = npma_count_masked(data_scl[0, :, :])  # Outside geojson
    mask_scl_stats[A3] = mask_scl_stats[A1] / (mask_scl_stats[A1] + mask_scl_stats[A2]) * 100
    mask_scl_stats[A4] = mask_scl_stats[A2] / (mask_scl_stats[A1] + mask_scl_stats[A2]) * 100

    # B_: Total unmasked (valid) and masked (invalid) within geojson
    if mask_scl and whitelist:
        scl_wl = mask_scl
    elif mask_scl and whitelist is False:
        scl_wl = set(SCL) - set(mask_scl)
    else:
        scl_wl = None
        mask_scl_stats[B1] = None
        mask_scl_stats[B2] = None
        mask_scl_stats[B3] = None
        mask_scl_stats[B4] = None

    if scl_wl:
        mask_scl_stats[B1] = np_count_nonzero(
            np_isin(data_scl.data[0, :, :], scl_wl)
        )  # count of pixels in scl_wl (not including geojson mask)
        mask_scl_stats[B2] = (
            mask_scl_stats[A1] - mask_scl_stats[B1]
        )  # count of pixels NOT in scl_wl (not including geojson mask)
        # invalid_mask_scl_pix + valid_mask_scl_pix  # should equal sum(list(mask_scl_stats[C1].values())) - mask_scl_stats[C1]["GEOJSON_MASK"]
        mask_scl_stats[B3] = mask_scl_stats[B1] / (mask_scl_stats[B1] + mask_scl_stats[B2]) * 100
        mask_scl_stats[B4] = mask_scl_stats[B2] / (mask_scl_stats[B1] + mask_scl_stats[B2]) * 100

    # C_: Breakdown of SCL classes within geojson
    mask_scl_stats[C1] = {scl.name: np_count_nonzero(data_scl.data[0, :, :] == scl) for scl in SCL}
    mask_scl_stats[C2] = {
        scl.name: (np_count_nonzero(data_scl.data[0, :, :] == scl) / mask_scl_stats[A1]) * 100 for scl in SCL
    }
    mask_scl_stats[C1]["NO_DATA"] = mask_scl_stats[C1]["NO_DATA"] - mask_scl_stats[A2]
    mask_scl_stats[C2]["NO_DATA"] = (mask_scl_stats[C1]["NO_DATA"] / mask_scl_stats[A1]) * 100
    return mask_scl_stats


def mask_stac_crop(data: ArrayLike, profile: Profile, nodata: Union[float, int] = 0) -> tuple[np_ndarray, Profile]:
    """Sets the last band of <data> as a mask layer, setting nodata.

    Note:
        The pixels.sentera.com/stac/crop/abc...xyz.tif endpoint returns a 3D array, with the 3rd dimension being a
        binary (0 or 255) mask band. This function does two things:

            - Adjusts data so the 1st dimension (number of bands) has a similar length to the number of bands.
            - Applies the pixels.sentera.com mask band to a numpy.mask

    Note:
        rasterio.DataSetReader.read() returns array with shape (bands, rows, columns)

    mask2 = None
    # Could we always request the SCL layer with request_crop so we know what is outside geojson and what is actually
    # masked? Problem is that they both show up as "nodata". Better to probably get SCL specifically if/when it is
    # needed.

    Options:
        1. Get SCL separately before or at the time mask_stac_crop is called (messy)
        2. Have separate function that uses geojson to calculate number and proportion of intersecting pixels per band.
            - The difference between

    """
    nodata = 0 if nodata is None else nodata

    mask = np_expand_dims(data[-1, :, :], axis=0)  # stac/crop mask
    data_no_alpha = data[:-1, :, :]  # get all but last band
    # data_no_alpha[np_repeat(mask, data_no_alpha.shape[0], axis=0) == 0.0] = ma.masked
    array_mask = ma.masked_array(data_no_alpha, mask=np_logical_not(np_repeat(mask, data_no_alpha.shape[0], axis=0)))
    # array_mask = ma.masked_array(data_no_alpha, mask=np_logical_not(mask))

    if not ma.maximum_fill_value(array_mask) <= nodata <= ma.minimum_fill_value(array_mask):
        array_mask = array_mask.astype(np_min_scalar_type(nodata))  # set array dtype so nodata is valid
    ma.set_fill_value(array_mask, nodata)
    profile.update(nodata=nodata)

    array_mask, profile = ensure_data_profile_consistency(array_mask, profile, driver=profile["driver"])
    return array_mask, profile


@requires_rasterio
def parse_crop_response(r: STAC_crop, **kwargs) -> Tuple[ArrayLike, Profile]:
    nodata = kwargs.get("nodata")  # gets value if key exists, else sets to None
    with Env(), response_to_rasterio(r) as ds:
        data = ds.read(masked=False)
        profile = ds.profile
        tags = ds.tags()
    data_mask, profile_mask = mask_stac_crop(data, profile, nodata=nodata)
    tags.update(**profile_mask)
    tags.update(**kwargs)
    # profile_mask.update(**kwargs)
    return data_mask, profile_mask, tags


def rescale_stac_crop(data: ArrayLike, rescale: Iterable[str], dtype: DTypeLike) -> ArrayLike:
    """
    Rescales STAC crop data.

    Args:
        data (ArrayLike): Data to be scaled (should be 3-dimensional).
        rescale (Iterable[str]): How to scale the data. Should be formatted as an iterable of strings, where the number
        of strings is equal to the length of the first dimension of `data`. Each string should be a comma-separated
        integer, expressed as a string (e.g., ["0,255", "0,255", "0,255"]). This example presumes `data` has 3 bands,
        and will rescale each of its 3 bands between 0 and 255.
        dtype (DTypeLike): The dtype to format the scaled data.

    Raises:
        RuntimeError: If `rescale` is not formatted properly.

    Returns:
        ArrayLike: The scaled data array.
    """
    data_scaled = zeros_like(data, dtype=dtype)
    if len(rescale) == data.shape[0]:
        for i, limits in enumerate(rescale):
            assert len(limits.split(",")) == 2
            # l = int(limits.split(",")[0])
            # u = int(limits.split(",")[1])
            # scale_factor = 10000 / (u - l)
            # data_scaled[i, :, :] = (data[i, :, :].data - l) / scale_factor
            lower = data[i, :, :].data.min()
            upper = data[i, :, :].data.max()
            max_value = int(limits.split(",")[1])
            # min_value = int(limits.split(",")[0])
            data_scaled[i, :, :] = (data[i, :, :].data - lower) / (upper - lower) * max_value
    else:
        raise RuntimeError("<rescale> argument must be the same length as data ({data.shape[0]}).")
    return data_scaled


@requires_rasterio
def response_to_rasterio(r: STAC_crop) -> DatasetReader:
    """Parses STAC_crop response into rasterio dataset.

    Args:
        r (STAC_crop): _description_

    Example:
        >>> with Env(), response_to_rasterio(r.content) as ds:
        >>>     data = ds.read()
        >>>     profile = ds.profile
        >>>     tags = ds.tags()

    Returns:
        DatasetReader: _description_
    """
    with MemoryFile(r.content) as m:
        ds = m.open()
    return ds


def write_to_file(path: str, data: ArrayLike, profile: Profile):
    """
    path = "/mnt/c/Users/Tyler/Downloads/test2.tif"
    """
    # data_out = data[0]
    save_image(data, profile, path, driver="Gtiff", keep_xml=False)

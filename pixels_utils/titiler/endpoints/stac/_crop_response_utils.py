from io import BytesIO
from typing import Dict, Iterable, Tuple, Union

import numpy.ma as ma
from numpy import count_nonzero as np_count_nonzero
from numpy import expand_dims as np_expand_dims
from numpy import isin as np_isin
from numpy import load as np_load
from numpy import logical_not as np_logical_not
from numpy import min_scalar_type as np_min_scalar_type
from numpy import ndarray as np_ndarray
from numpy import repeat as np_repeat
from numpy import zeros_like
from numpy.ma import count as npma_count
from numpy.ma import count_masked as npma_count_masked
from numpy.typing import ArrayLike, DTypeLike
from rasterio import Env
from rasterio.errors import RasterioIOError
from rasterio.io import DatasetReader, MemoryFile
from rasterio.profiles import DefaultGTiffProfile, Profile

from pixels_utils.constants.types import STAC_crop
from pixels_utils.rasterio_helper import ensure_data_profile_consistency, save_image
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


def crop_set_mask(data: ArrayLike, profile: Profile, nodata: Union[float, int] = 0) -> tuple[np_ndarray, Profile]:
    """Sets the last band of <data> as a mask layer, setting nodata.

    Note:
        The pixels.sentera.com/stac/crop/abc...xyz.tif endpoint returns a 3D array, with the 3rd dimension being a
        binary (0 or 255) mask band. This function does two things:

            - Adjusts data so the 1st dimension (number of bands) has a similar length to the number of bands.
            - Applies the pixels.sentera.com mask band to a numpy.mask

        rasterio.DataSetReader.read() returns array with shape (bands, rows, columns)

    Args:
        data (ArrayLike): Data array. Must be 3-dimensional.
        profile (Profile): Rasterio Profile for data array.
        nodata (Union[float, int], optional): Nodata value. Defaults to 0.

    Returns:
        tuple[np_ndarray, Profile]: Masked data array and corresponding Rasterio Profile.
    """
    assert data.ndim == 3, f"Array must be 3-dimensional (passed array has {data.ndim} dimensions)."
    nodata = 0 if nodata is None else nodata

    mask = np_expand_dims(data[-1, :, :], axis=0)  # stac/crop mask
    data_no_alpha = data[:-1, :, :]  # get all but last band
    array_mask = ma.masked_array(data_no_alpha, mask=np_logical_not(np_repeat(mask, data_no_alpha.shape[0], axis=0)))

    if not ma.maximum_fill_value(array_mask) <= nodata <= ma.minimum_fill_value(array_mask):
        array_mask = array_mask.astype(np_min_scalar_type(nodata))  # set array dtype so nodata is valid
    ma.set_fill_value(array_mask, nodata)
    profile.update(nodata=nodata)

    array_mask, profile = ensure_data_profile_consistency(array_mask, profile, driver=profile["driver"])
    return array_mask, profile


def parse_crop_response(r: STAC_crop, **kwargs) -> Tuple[ArrayLike, Profile]:
    read_kwargs = {}
    read_kwargs["out_dtype"] = kwargs.get("dtype") if "dtype" in kwargs.keys() else None
    read_kwargs = {k: v for k, v in read_kwargs.items() if v is not None}

    try:
        with Env(), response_to_rasterio(r) as ds:
            data = ds.read(masked=False, **read_kwargs)
            profile = ds.profile
            profile["band_names"] = kwargs.get("band_names") if "band_names" in kwargs.keys() else None
            tags = ds.tags()
    except RasterioIOError:
        data = np_load(BytesIO(r.content))
        # TODO: ensure_data_profile_consistency()
        profile, tags = DefaultGTiffProfile(), {}  # npy doesn't provide profile information

    nodata = kwargs.get("nodata")  # gets value if key exists, else sets to None
    data_mask, profile_mask = crop_set_mask(data, profile, nodata=nodata)
    tags.update(**profile_mask)
    tags.update(**kwargs)
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

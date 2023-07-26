from io import BytesIO
from typing import Dict, Iterable, Tuple, Union

import numpy.ma as ma
from numpy import expand_dims as np_expand_dims
from numpy import load as np_load
from numpy import logical_not as np_logical_not
from numpy import min_scalar_type as np_min_scalar_type
from numpy import ndarray as np_ndarray
from numpy import repeat as np_repeat
from numpy import zeros_like
from numpy.typing import ArrayLike, DTypeLike
from rasterio import Env
from rasterio.errors import RasterioIOError
from rasterio.io import DatasetReader, MemoryFile
from rasterio.profiles import DefaultGTiffProfile, Profile

from pixels_utils.constants.types import STAC_crop
from pixels_utils.rasterio_helper import ensure_data_profile_consistency, save_image


def _crop_set_mask(data: ArrayLike, profile: Profile, nodata: Union[float, int] = 0) -> tuple[np_ndarray, Profile]:
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

    # By default titiler will return a concatenated data,mask array.
    data_no_alpha, mask = data[:-1, :, :], np_expand_dims(data[-1, :, :], axis=0)
    array_mask = ma.masked_array(data_no_alpha, mask=np_logical_not(np_repeat(mask, data_no_alpha.shape[0], axis=0)))

    if not ma.maximum_fill_value(array_mask) <= nodata <= ma.minimum_fill_value(array_mask):
        array_mask = array_mask.astype(np_min_scalar_type(nodata))  # set array dtype so nodata is valid
    ma.set_fill_value(array_mask, nodata)
    profile.update(nodata=nodata)

    array_mask, profile = ensure_data_profile_consistency(array_mask, profile, driver=profile["driver"])
    return array_mask, profile


def _response_to_rasterio(r: STAC_crop) -> DatasetReader:
    """Parses STAC_crop response into rasterio dataset.

    Args:
        r (STAC_crop): _description_

    Example:
        >>> with Env(), _response_to_rasterio(r.content) as ds:
        >>>     data = ds.read()
        >>>     profile = ds.profile
        >>>     tags = ds.tags()

    Returns:
        DatasetReader: _description_
    """
    with MemoryFile(r.content) as m:
        ds = m.open()
    return ds


def parse_crop_response(r: STAC_crop, **kwargs) -> Tuple[ArrayLike, Profile, Dict]:
    """
    Parses STAC_crop response into a masked data array, rasterio profile, and rasterio tags.

    Args:
        r (STAC_crop): STAC crop response to parse.
        kwargs: Additional keyword arguments used to control the output masked data array and rasterio profile. Specific
        keywords used by this function include `dtype`, `band_names`, and `nodata`. Other keywords are passed to the
        output `tags` dictionary.

    Returns:
        Tuple[ArrayLike, Profile, Dict]: Parsed response objects.
    """
    read_kwargs = {}
    read_kwargs["out_dtype"] = kwargs.get("dtype") if "dtype" in kwargs.keys() else None
    read_kwargs = {k: v for k, v in read_kwargs.items() if v is not None}

    try:
        with Env(), _response_to_rasterio(r) as ds:
            data = ds.read(masked=False, **read_kwargs)
            profile = ds.profile
            profile["band_names"] = kwargs.get("band_names") if "band_names" in kwargs.keys() else None
            tags = ds.tags()
    except RasterioIOError:
        data = np_load(BytesIO(r.content))
        # TODO: ensure_data_profile_consistency()
        profile, tags = DefaultGTiffProfile(), {}  # npy doesn't provide profile information

    nodata = kwargs.get("nodata")  # gets value if key exists, else sets to None
    data_mask, profile_mask = _crop_set_mask(data, profile, nodata=nodata)
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


def write_to_file(path: str, data: ArrayLike, profile: Profile):
    """
    path = "/mnt/c/Users/Tyler/Downloads/test2.tif"
    """
    # data_out = data[0]
    save_image(data, profile, path, driver="Gtiff", keep_xml=False)

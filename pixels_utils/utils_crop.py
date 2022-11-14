import logging
from typing import Union

import numpy.ma as ma
from numpy import expand_dims as np_expand_dims
from numpy import logical_not as np_logical_not
from numpy import min_scalar_type as np_min_scalar_type
from numpy import ndarray as np_ndarray
from numpy import repeat as np_repeat
from numpy.typing import ArrayLike

from pixels_utils.constants.decorators import requires_rasterio
from pixels_utils.constants.types import STAC_crop

try:
    from rasterio.io import DatasetReader, MemoryFile
    from rasterio.profiles import Profile

    from pixels_utils.rasterio_helper import ensure_data_profile_consistency, save_image
except ImportError:
    logging.exception("Optional dependency <rasterio> not imported. Some features are not available.")


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

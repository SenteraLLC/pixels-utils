import logging
from contextlib import suppress
from os import remove as os_remove
from os.path import dirname, split
from pathlib import Path
from typing import List

import numpy.typing as npt
from rasterio import Env
from rasterio import open as rio_open
from rasterio.dtypes import check_dtype
from rasterio.io import DatasetReader
from rasterio.profiles import Profile


# TODO: Most (if not all) of these fucntions can be ported over to `geo_utils` repo.
def combine_profile_tags(ds: DatasetReader) -> Profile:
    return ds.tags() | ds.profile.copy()


def set_driver_tags(profile: Profile, driver: str = "Gtiff", interleave: str = None) -> Profile:
    if driver == "ENVI":
        if interleave not in ["bip", "bsq", "bil"]:
            raise ValueError('`interleave` must be one of ["bip", "bsq", "bil"].')
        profile["SUFFIX"] = "ADD"
        profile["INTERLEAVE"] = interleave.upper()
    elif driver == "Gtiff":
        profile["INTERLEAVE"] = "PIXEL"
        profile["COMPRESS"] = "NONE"
    elif driver == "PostGISRaster":  # provides read-only support to PostGIS raster data sources
        raise AttributeError('"PostGISRaster" provides read-only support.')
    return profile


def ensure_data_profile_consistency(
    array: npt.ArrayLike,
    profile: Profile,
    driver: str = "Gtiff",
    # nodata: Union[float, int] = 0,
) -> tuple[Profile, npt.ArrayLike]:
    profile.update(
        driver=driver,
        count=array.shape[0],
        height=array.shape[1],
        width=array.shape[2],
        dtype=array.dtype,
        # nodata=nodata,
    )
    profile.update(nodata=array.get_fill_value()) if profile["nodata"] is not None else None
    try:
        array = array.astype(profile["dtype"])
    except KeyError:
        if check_dtype(array.dtype):
            profile.update(dtype=array.dtype)
        else:
            raise ValueError(f'"{array.dtype}" is not a valid dtype for <array>.')
    return array, profile


def get_band_description(profile: Profile) -> List:
    """
    Gets band description (to be set by rasterio.DatasetReader.set_band_description).

    Args:
        profile: Profile containing. Should contain "band_names", "wavelength", and
        "wavelength_units" keys. At a minimum, must contain "wavelength", "band_names",
        or "count" keys.

    Returns:
        band_descriptions (list): A list of strings that can be passed
            iteratively to ``dst.set_band_description()``.
    """
    if "band_names" in profile.keys() and "wavelength" in profile.keys() and "wavelength_units" in profile.keys():
        band_labels = [
            f"{b}: {wl} {profile['wavelength_units']}" for b, wl in zip(profile["band_names"], profile["wavelength"])
        ]
    elif "wavelength" in profile.keys():
        wl_units = profile["wavelength_units"] if "wavelength_units" in profile.keys() else "nm"
        band_labels = [f"{wl} {wl_units}" for wl in profile["wavelength"]]
    elif "band_names" in profile.keys():
        profile["band_names"] = (
            [profile["band_names"]] if isinstance(profile["band_names"], str) else profile["band_names"]
        )
        band_labels = [f"{band}" for band in profile["band_names"]]
    elif "count" in profile.keys():
        band_labels = [f"Band {b+1}" for b in range(profile["count"])]
    return band_labels


def save_image(
    array: npt.ArrayLike,
    profile: Profile,
    fname_out: str,
    driver: str = "Gtiff",
    interleave: str = None,
    keep_xml: bool = False,
):
    """Saves image array to disk with each <profile> items stored as tags.

    Args:
        array: Data array to save.
        profile: Rasterio Profile corresponding to ``array``.
        fname_out: The output filename.

        driver: The driver used to save the image array. Must be one of ["ENVI",
            "Gtiff"]. The default is "Gtiff".

        interleave (str): The intereave format to save image. Ignored if `driver` is
            not "ENVI". Defaults to None.

        keep_xml: When rasterio creates a new geotiff file, it creates an .xml file as
            well. Setting ``keep_xml`` to ``False`` deletes the .xml upon creation to
            avoid clutter in the folder directory. The default is False.

    Raises:
        AttributeError: If driver is set to "PostGISRaster" (not yet supported).
    """
    assert array.ndim == 3, f"Array must be 3-dimensional (passed array has {array.ndim} dimensions)."
    try:
        Path(dirname(fname_out)).mkdir(parents=True, exist_ok=True)
    except FileExistsError:  # get this every once in a while for .tif
        pass
    logging.debug('Saving "%s"', split(fname_out)[-1])

    profile = set_driver_tags(profile, driver, interleave)
    array, profile = ensure_data_profile_consistency(array, profile, driver)
    band_descriptions = get_band_description(profile)

    with Env(), rio_open(fname_out, "w", **profile) as rast_out:
        rast_out.write(array)  # write raster first
        [rast_out.set_band_description(i + 1, info) for i, info in enumerate(band_descriptions)][0]
        rast_out.update_tags(**profile)
    if driver == "ENVI":  # and now update header if ENVI format
        # write_envi(array, profile, fname_out)
        logging.warning("Not yet pulled from Insight db-geoml/utilities.py")
    if keep_xml is False:
        fname_xml = Path(str(fname_out) + ".aux.xml")
        # fname_xml = fname_out + ".aux.xml"
        with suppress(FileNotFoundError):
            os_remove(fname_xml)

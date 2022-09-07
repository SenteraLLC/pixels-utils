import logging
from contextlib import suppress
from os import remove as os_remove
from os.path import dirname, split
from pathlib import Path
from typing import List
from warnings import warn

import numpy.typing as npt

from pixels_utils.constants.decorators import requires_rasterio

try:
    from rasterio import Env
    from rasterio import open as rio_open
    from rasterio.dtypes import check_dtype
    from rasterio.io import DatasetReader
    from rasterio.profiles import Profile
except ImportError:
    warn(
        "Optional dependency <rasterio> not imported. Some features are not available."
    )


# TODO: Most (if not all) of these fucntions can be ported over to `geo_utils` repo.
@requires_rasterio
def combine_profile_tags(ds: DatasetReader) -> Profile:
    return ds.tags() | ds.profile.copy()


@requires_rasterio
def set_driver_tags(
    profile: Profile, driver: str = "Gtiff", interleave: str = None
) -> Profile:
    if driver == "ENVI":
        if interleave not in ["bip", "bsq", "bil"]:
            raise ValueError('`interleave` must be one of ["bip", "bsq", "bil"].')
        profile["SUFFIX"] = "ADD"
        profile["INTERLEAVE"] = interleave.upper()
    elif driver == "Gtiff":
        profile["INTERLEAVE"] = "PIXEL"
        profile["COMPRESS"] = "NONE"
    elif (
        driver == "PostGISRaster"
    ):  # provides read-only support to PostGIS raster data sources
        raise AttributeError('"PostGISRaster" provides read-only support.')
    return profile


@requires_rasterio
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
    profile.update(nodata=array.get_fill_value()) if profile[
        "nodata"
    ] is not None else None
    try:
        array = array.astype(profile["dtype"])
    except KeyError:
        if check_dtype(array.dtype):
            profile.update(dtype=array.dtype)
        else:
            raise ValueError(f'"{array.dtype}" is not a valid dtype for <array>.')
    return array, profile


@requires_rasterio
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
    if (
        "band_names" in profile.keys()
        and "wavelength" in profile.keys()
        and "wavelength_units" in profile.keys()
    ):
        band_labels = [
            f"{b}: {wl} {profile['wavelength_units']}"
            for b, wl in zip(profile["band_names"], profile["wavelength"])
        ]
    elif "wavelength" in profile.keys():
        band_labels = [
            f"{wl} {profile['wavelength_units']}" for wl in profile["wavelength"]
        ]
    elif "band_names" in profile.keys():
        if isinstance(profile["band_names"], str):
            profile["band_names"] = [profile["band_names"]]
        band_labels = [f"{band}" for band in profile["band_names"]]
    elif "count" in profile.keys():
        band_labels = ["Band {0}".format(b + 1) for b in range(profile["count"])]
    return band_labels


@requires_rasterio
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
    try:
        Path(dirname(fname_out)).mkdir(parents=True, exist_ok=True)
    except FileExistsError:  # get this every once in a while for .tif
        pass
    logging.info('Saving "%s"', split(fname_out)[-1])

    profile = set_driver_tags(profile, driver, interleave)
    array, profile = ensure_data_profile_consistency(array, profile, driver)
    band_descriptions = get_band_description(profile)

    with Env(), rio_open(fname_out, "w", **profile) as rast_out:
        rast_out.write(array)  # write raster first
        [
            rast_out.set_band_description(i + 1, info)
            for i, info in enumerate(band_descriptions)
        ][0]
        rast_out.update_tags(**profile)
    if driver == "ENVI":  # and now update header if ENVI format
        # write_envi(array, profile, fname_out)
        logging.info("Not yet pulled from Insight db-geoml/utilities.py")
    if keep_xml is False:
        fname_xml = fname_out + ".aux.xml"
        with suppress(FileNotFoundError):
            os_remove(fname_xml)


# @requires_rasterio
# def geoml_metadata(
#     array_img,
#     profile_in,
#     scene,
#     stac_url,
#     gsd,
#     cloud_shad_pct,
#     assets=None,
#     expression=None,
#     assets_name=None,
#     expression_name=None,
# ):
#     """
#     Gets complete metadata from STACReader assets.
#     Args:
#         array_img (ndarray): Array to save.
#         profile_in (dict): The metadata dictionary that corresponds to `array` (can be
#         derived from another image file via `rasterio.io.DatasetReader.meta`).
#         scene (dict): DESCRIPTION.
#         stac_url (str): The STAC-url where imagery was originally retrieved from.
#         gsd (int): Ground sampling distance of original `array_img` (in meters).
#         cloud_shad_pct (float): The percent cloud + shadow in the image to append to
#         the metadata.
#         assets (list-like, optional): STACReader assests to return. Defaults to None.
#         expression (str, optional): DESCRIPTION. Defaults to None.
#         assets_name (str, optional): DESCRIPTION. Defaults to None.
#         expression_name (str, optional): DESCRIPTION. Defaults to None.
#     Returns:
#         metadata (dict): Rasterio metadata dictionary.
#     """
#     assets_name, expression_name = check_assets_expression(
#         assets, expression, assets_name=assets_name, expression_name=expression_name
#     )

#     metadata = deepcopy(create_meta(array_img, profile_in))
#     tile = scene["id"].split("_")[1]
#     product = scene["id"].split("_")[4]
#     if assets_name is not None:
#         product_str = "{0}_{1}".format(assets_name, product)
#     else:
#         product_str = "{0}_{1}".format(expression_name, product)
#     if cloud_shad_pct is None:
#         cloud_shad_pct = "NULL"  # Maybe this is better as `None`?
#     metadata["url"] = stac_url
#     metadata["sensor type"] = "Sentinel"
#     metadata["acquisition time"] = scene["properties"]["datetime"]
#     metadata["description"] = {"tile": tile, "product": product_str}
#     # metadata['product'] = product_str  # Not an ENVI header tag
#     metadata["samples"] = metadata["width"]  # For ENVI .hdr compatibility
#     metadata["lines"] = metadata["height"]  # For ENVI .hdr compatibility
#     metadata["bands"] = metadata["count"]
#     metadata["header offset"] = 0
#     metadata["data ignore value"] = metadata["nodata"]
#     metadata["map info"] = None  # If projected (UTM); set by spectral.envi
#     metadata["coordinate system string"] = profile_in[
#         "crs"
#     ].to_wkt()  # Can also be set by spectral.envi
#     metadata["cloud cover"] = cloud_shad_pct  # cloud + cloud shadow percent (0-100)
#     metadata["pixel size"] = [gsd, gsd]
#     metadata["wavelength_units"] = "nanometers"
#     if assets is not None:
#         metadata["band_names"] = esa_scene_metadata(scene, assets, meta_item="name")
#         metadata["wavelength"] = esa_scene_metadata(
#             scene, assets, meta_item="center_wavelength", unit="nanometer"
#         )
#         metadata["fwhm"] = esa_scene_metadata(
#             scene, assets, meta_item="full_width_half_max", unit="nanometer"
#         )
#         metadata["reflectance scale factor"] = 10000  # New
#     else:
#         metadata["band_names"] = expression_name
#     return metadata

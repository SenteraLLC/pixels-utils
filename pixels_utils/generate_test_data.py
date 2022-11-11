import itertools
import logging
import pickle
from os.path import abspath, join
from pathlib import Path

from pixels_utils.constants.sentinel2 import (
    ASSETS_MSI,
    EXPRESSION_NDVI,
    SCL_GROUP_ARABLE,
)
from pixels_utils.endpoints.stac import statistics
from pixels_utils.tests.data.load_data import sample_geojson, sample_scene_url


class GenerateTestData:
    """
    Step 0: Determine all combinations and give each a name
    Step 1: choose assets and expression
    Step 2: iterate through combinations and create for assets/expression combination.

    Example:
        >>> from pixels_utils.generate_test_data import GenerateTestData
        >>> data_generator = GenerateTestData(geojson_id=1)
        >>> data_generator.generate_statistics()
    """

    def __init__(self, geojson_id=1, dir_test_data=None):
        self.geojson_id = geojson_id
        if dir_test_data is None:
            self.dir_test_data = join(
                abspath(Path(__file__).resolve().parents[0]),
                "tests",
                "data",
                "statistics",
            )

    def _get_combinations(self):
        return list(
            itertools.product(
                *[
                    [sample_scene_url(self.geojson_id)],
                    [None, ASSETS_MSI],
                    [None, EXPRESSION_NDVI],
                    [None, sample_geojson(1)["features"][0]],
                    [None, SCL_GROUP_ARABLE],
                    [True, False],
                    [None, -1],
                    [None, 10, 20],
                ]
            )
        )

    def _get_names(self, assets, expression, geojson, mask_scl, whitelist, nodata, gsd):
        assets_name = "MSI" if assets == ASSETS_MSI else "None"
        expression_name = "NDVI" if expression == EXPRESSION_NDVI else "None"
        geo_name = f"aoi{self.geojson_id}" if geojson is not None else "None"
        if mask_scl is not None and whitelist is True:
            scl_mask_name = "wl"
        elif mask_scl is not None and whitelist is False:
            scl_mask_name = "bl"
        else:
            scl_mask_name = "None"

        folder = f"ASSETS_{assets_name}_EXPRESSION_{expression_name}_GSD_{gsd}"
        name = f"geo_{geo_name}_scl_mask_{scl_mask_name}"
        name = f"{name}_nodata" if nodata is not None else name
        return folder, name

    def _save_pickle(self, r, folder, name):
        Path(join(self.dir_test_data, folder)).mkdir(parents=True, exist_ok=True)
        f = join(self.dir_test_data, folder, f"{name}.pickle")
        with open(f, "wb") as filehandler:
            pickle.dump(r, filehandler)

    def generate_statistics(self):
        for (
            scene_url,
            assets,
            expression,
            geojson,
            mask_scl,
            whitelist,
            nodata,
            gsd,
        ) in self._get_combinations():
            if mask_scl is None and whitelist is False:
                continue  # because this same scenario is covered for whitelist = True
            folder, name = self._get_names(
                assets, expression, geojson, mask_scl, whitelist, nodata, gsd
            )
            logging.debug("Generating sample data for %s/%s", folder, name)
            try:
                r = statistics(
                    scene_url,
                    assets=assets,
                    expression=expression,
                    geojson=geojson,
                    mask_scl=mask_scl,
                    whitelist=whitelist,
                    nodata=nodata,
                    gsd=gsd,
                    resampling="nearest",
                )
                self._save_pickle(r, folder, name)
            except ValueError:
                logging.exception(
                    "Unable to generate sample data (invalid arguments): ValueError"
                )
            except NotImplementedError:
                logging.exception(
                    "Unable to generate sample data (NotImplementedError): NotImplementedError"
                )

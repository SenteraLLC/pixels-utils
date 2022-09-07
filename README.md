# pixels-utils

A pythonic data science wrapper to [Sentera's public satellite imagery API](https://pixels.sentera.com). The main purpose is to provide more direct access to the Pixels API via common data science libraries (like Pandas and GeoPandas).

## Setup and Installation (for development)
1) [Set up SSH](https://github.com/SenteraLLC/install-instructions/blob/master/ssh_setup.md)
2) Install [pyenv](https://github.com/SenteraLLC/install-instructions/blob/master/pyenv.md) and [poetry](https://python-poetry.org/docs/#installation).
3) Install package
``` bash
git clone git@github.com:SenteraLLC/pixels-utils.git
cd pixels-utils
pyenv install $(cat .python-version)
poetry config virtualenvs.in-project true
poetry env use $(cat .python-version)
poetry install
```
4) Set up `pre-commit` to ensure all commits to adhere to **black** and **PEP8** style conventions.
``` bash
poetry run pre-commit install
```

## Setup and Installation (used as a library)
If using `pixels-utils` as a dependency in your script, simply add it to the `pyproject.toml` in your project repo. Be sure to uuse the `ssh:` prefix so Travis has access to the repo for the library build process.

<h5 a><strong><code>pyproject.toml</code></strong></h5>

``` toml
[tool.poetry.dependencies]
pixels_utils = { git = "ssh://git@github.com/SenteraLLC/pixels-utils.git", branch = "main", extras = ["rasterio"]}
```

Install `pixels-utils` and all its dependencies via `poetry install`.

``` console
poetry install
```

## Usage Example

### Example 1 - Get cloud-masked statistics for a geometry

<h5 a><strong><code>pixels_utils_statistics_geojson.py</code></strong></h5>

``` python
from pixels_utils.endpoints.stac import statistics
from pixels_utils.constants.sentinel2 import (
    ELEMENT84_L2A_SCENE_URL,
    SENTINEL_2_L2A_COLLECTION,
    EXPRESSION_NDVI,
)
from pixels_utils.constants.titiler import ENDPOINT_STATISTICS
from pixels_utils.mask import SCL
from pixels_utils.tests.data import sceneid, sample_geojson
from pixels_utils.utilities import _check_assets_expression

scene_url = ELEMENT84_L2A_SCENE_URL.format(
    collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid
)
assets=None
expression=EXPRESSION_NDVI
mask_scl = [SCL.VEGETATION, SCL.BARE_SOIL]
geojson = sample_geojson()["features"][0]
whitelist=True
nodata=None

r = statistics(
    scene_url,
    assets=assets,
    expression=expression,
    geojson=geojson,
    mask_scl=mask_scl,
    whitelist=whitelist,
    nodata=nodata,
)

pprint(r.json()["properties"][ENDPOINT_STATISTICS])
```

<h5 a><code>[OUTPUT]</code></h5>

``` python
{'where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0.0))': {
    'count': 1021.0,
    'histogram': [<omitted for brevity>],
    'majority': 0.14285714285714285,
    'masked_pixels': 1487.0,
    'max': 0.24060150375939848,
    'mean': 0.14380032393285688,
    'median': 0.14462416745956233,
    'min': 0.105562855891371,
    'minority': 0.105562855891371,
    'percentile_2': 0.11589278323054499,
    'percentile_98': 0.16414680642034107,
    'std': 0.0121265938833696,
    'sum': 146.82013073544687,
    'unique': 802.0,
    'valid_percent': 40.71,
    'valid_pixels': 1021.0
}}
```

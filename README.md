# pixels-utils

A python wrapper to [Sentera's public Titiler imagery API](https://pixels.sentera.com). The main purpose is to provide more direct access to the Pixels API via common data science libraries (like Rasterio and GeoPandas).

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
### Release/Tags
- A GitHub release is created on every push to the main branch using the `create_github_release.yml` Github Action Workflow
- Releases can be created manually through the GitHub Actions UI as well.
- The name of the Release/Tag will match the value of the version field specified in `pyproject.toml`
- Release Notes will be generated automatically and linked to the Release/Tag

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

### Logging style
This library uses the `"%s"` [logging.Formatter() style](https://docs.python.org/3/library/logging.html#logging.Formatter). For logging messages to show up, style should be set as `style="%s"` (this is the default). The recommended approach is to use the `logging_init()` function from [py-utils](https://github.com/SenteraLLC/py-utils).

For example:

``` python
import logging
from utils.logging.tqdm import logging_init

if __name__ == "__main__":
    logging_init(
        level=logging.INFO,
        format_string="{name} - {levelname}: {message}",
        style="%"
    )
```

## Usage Example

### Example 1 - Find all the scenes available for a geometry within a date range

<h5 a><strong><code>pixels_utils_scene_search.py</code></strong></h5>

``` python
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pixels_utils.constants.titiler import ENDPOINT_STATISTICS
from pixels_utils.mask import SCL


from geo_utils.vector import geojson_geometry_to_shapely

from pixels_utils.tests.data.load_data import sample_geojson
from pixels_utils.scenes import get_stac_scenes

DATA_ID = 1

geojson = sample_geojson(DATA_ID)

scenes = get_stac_scenes(
    bounding_box=geojson_geometry_to_shapely(geojson).bounds,
    date_start= "2019-01-01",
    date_end= "2019-01-31",
    max_scene_cloud_cover_percent = 80,
)

pprint(r.json()["properties"][ENDPOINT_STATISTICS])
```

<h5 a><code>[OUTPUT]</code></h5>

| index | id                       | datetime             | eo:cloud_cover |
| ----- | ------------------------ | -------------------- | -------------- |
| 0     | S2B_10TGS_20190125_0_L2A | 2019-01-25T19:01:37Z |          45.17 |
| 1     | S2A_10TGS_20190110_0_L2A | 2019-01-10T19:01:32Z |          56.59 |
| 2     | S2A_11TLM_20190110_0_L2A | 2019-01-10T19:01:30Z |          24.87 |


### Example 2 - Get cloud-masked statistics for a geometry

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

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


### Catalog Documentation
[Earth Search STAC API](https://github.com/Element84/earth-search) (maintained by [Element 84](https://element84.com/))


### Release/Tags
- A GitHub release is created on every push to the main branch using the `create_github_release.yml` Github Action Workflow
- Releases can be created manually through the GitHub Actions UI as well.
- The name of the Release/Tag will match the value of the version field specified in `pyproject.toml`
- Release Notes will be generated automatically and linked to the Release/Tag


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
[scripts/scene_search.py](https://github.com/SenteraLLC/pixels-utils/blob/main/scripts/scene_search.py)

```python
from pixels_utils.tests.data.load_data import sample_feature
from pixels_utils.scenes import parse_nested_stac_data, search_stac_scenes
from pixels_utils.stac_catalogs.earthsearch.v1 import EARTHSEARCH_URL, EarthSearchCollections


DATA_ID = 1

df_scenes = search_stac_scenes(
    geometry=sample_feature(DATA_ID),
    date_start="2019-01-01",
    date_end="2019-01-31",
    stac_catalog_url=EARTHSEARCH_URL,
    collection=EarthSearchCollections.sentinel_2_l2a,
    query={"eo:cloud_cover": {"lt": 80}},  # keeps less than 80% cloud cover,
    simplify_to_bbox=True,
)

print(
    df_scenes[["id"]]
    .merge(
        parse_nested_stac_data(df=df_scenes, column="properties")[["datetime", "eo:cloud_cover"]],
        left_index=True,
        right_index=True,
    )
    .to_markdown(tablefmt="pipe")
)
```

<h5 a><code>[OUTPUT]</code></h5>

|    | id                       | datetime                    |   eo:cloud_cover |
|---:|:-------------------------|:----------------------------|-----------------:|
|  0 | S2A_11TLM_20190110_0_L2A | 2019-01-10T19:01:30.135000Z |          26.9409 |
|  1 | S2A_10TGS_20190110_0_L2A | 2019-01-10T19:01:32.811000Z |          61.8212 |
|  2 | S2B_10TGS_20190125_0_L2A | 2019-01-25T19:01:37.534000Z |          55.6444 |

### Example 2 - Get cloud-masked statistics for a geometry
[scripts/statistics.py](https://github.com/SenteraLLC/pixels-utils/blob/main/scripts/statistics.py)

``` python
from pixels_utils.stac_catalogs.earthsearch.v1 import expression_from_collection, EarthSearchCollections
from pixels_utils.tests.data.load_data import sample_feature, sample_scene_url
from pixels_utils.titiler import TITILER_ENDPOINT
from pixels_utils.titiler.endpoints.stac import QueryParamsStatistics, Statistics, StatisticsPreValidation
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group

DATA_ID = 1

scene_url = sample_scene_url(data_id=DATA_ID)

collection_ndvi = expression_from_collection(collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI")

query_params = QueryParamsStatistics(
    url=scene_url,
    feature=sample_feature(DATA_ID),
    assets=None,  # ["nir"]
    expression=collection_ndvi.expression,  # "(nir-red)/(nir+red)"
    asset_as_band=True,
    asset_bidx=None,
    coord_crs=None,
    max_size=None,
    height=None,
    width=None,
    gsd=None,
    nodata=None,
    unscale=None,
    resampling=None,
    categorical=None,
    c=None,
    p=None,
    histogram_bins=None,
    histogram_range=None,
)

# Raises an AssertionError if any of the assets are not available for the query_params
# If you get a message "StatisticsPreValidation passed: all required assets are available.", you can proceed to Statistics
stats_preval = StatisticsPreValidation(query_params, titiler_endpoint=TITILER_ENDPOINT)


# Now actually request Statistics - for only arable pixels (whitelist=True)!
stats_arable_wlist = Statistics(
    query_params=query_params,  # collection_ndvi.expression - "(nir-red)/(nir+red)"
    titiler_endpoint=TITILER_ENDPOINT,
    mask_enum=Sentinel2_SCL_Group.ARABLE,
    mask_asset="scl",
    whitelist=True,
)

stats_arable_wlist.response.json()
```

<h5 a><code>[OUTPUT]</code></h5>

root - INFO - Item "S2B_10TGS_20220419_0_L2A" asset is AVAILABLE: "red".
root - INFO - Item "S2B_10TGS_20220419_0_L2A" asset is AVAILABLE: "nir".
root - INFO - StatisticsPreValidation PASSED. All required assets are available.
root - INFO - Adding masking parameters to `expression`.
{'type': 'Feature',
 'geometry': {'type': 'MultiPolygon',
  'coordinates': [[[[-119.036182, 46.239917],
     [-119.044517, 46.237081],
     [-119.044048, 46.239172],
     [-119.0413, 46.240763],
     [-119.036182, 46.239917]]]]},
 'properties': {'statistics': {'where(scl==4,(nir-red)/(nir+red),where(scl==5,(nir-red)/(nir+red),0.0))': {'min': 0.105562855891371,
    'max': 0.24060150375939848,
    'mean': 0.14380639335058598,
    'count': 1021.0,
    'sum': 146.82632761094828,
    'std': 0.01212996991547649,
    'median': 0.14462416745956233,
    'majority': 0.14285714285714285,
    'minority': 0.105562855891371,
    'unique': 801.0,
    'histogram': [<omitted for brevity>],
    'valid_percent': 40.71,
    'masked_pixels': 1487.0,
    'valid_pixels': 1021.0,
    'percentile_98': 0.16414680642034107,
    'percentile_2': 0.11589278323054499}}}}

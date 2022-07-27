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
pixels_utils = { git = "ssh://git@github.com/SenteraLLC/pixels-utils.git", branch = "main"}
```

Install `pixels-utils` and all its dependencies via `poetry install`.

``` console
poetry install
```

## Usage Example

### Step 1 - Add fields to FieldAgent

<h5 a><strong><code>gql_utils_add_fields.py</code></strong></h5>

``` python
from datetime import datetime
import json
import logging
from pixels_utils.fetch import getNameToExpression, getStats
from pixels_utils.scenes import getBoundingBox, getStacSceneItems

geojson =
date_start = "2022-05-01"
date_end = "2022-07-15"

bounding_box = getBoundingBox(geojson)
num_days = (datetime(date_end) - datetime(date_start)).days
logging.info(f"Fetching scenes for dates: {start_date} to {end_date} ({num_days} days)")
scene_items, summary = getStacSceneItems(bounding_box, date_start, date_end, max_scene_percent=100)

cloud_weights = getCloudWeights()
name_to_expression = getNameToExpression(cloud_weights)
stats, over_threshold = getStats(scene_items, geojson, name_to_expression, max_local_percent, cogs_url, pixels_url)
```

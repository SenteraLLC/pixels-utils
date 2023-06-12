# Support of New STAC Catalogs
- Add a new folder/directory under `stac_catalogs` that describes the catalog (e.g., `stac_catalogs/earthsearch`)
- Under the specific catalog directory, add a .py file that includes:
  - A variable containing the URL/endpoint (e.g., https://earth-search.aws.element84.com/v1)
  - An ENUM class that contains the available collections (for example, see [stac_catalogs/earthsearch/v1.py](https://github.com/SenteraLLC/pixels-utils/tree/main/pixels_utils/stac_catalogs/earthsearch/v1.py))
  - Store a .json of the URL/endpoint (for example, see [stac_catalogs/earthsearch/v1.json](https://github.com/SenteraLLC/pixels-utils/tree/main/pixels_utils/stac_catalogs/earthsearch/v1.json))
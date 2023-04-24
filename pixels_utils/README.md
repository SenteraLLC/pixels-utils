# Library Scope
Although the main purpose of `pixels-utils` is to provide more direct access to the Pixels API via common data science libraries (like Pandas and GeoPandas), it's always a challenge to decide where to draw the line between flexibility and ease-of-use. Here are some general guidelines followed during design of `pixels-utils` that describe that intended boundary.

## Within scope
- [x] Use [Sentera Pixels/TiTiler STAC endpoint](https://developmentseed.org/titiler/endpoints/stac/)  (e.g., `crop`, `statistics`, etc.) to request a STAC dataset and return data as the raw response, as if the query were passed directly to `pixels.sentera.com` using CURL or something similar.
- [x] Provide the user with the ability to retrieve data with full data integrity/accuracy (e.g., bypass any of the pyramiding/downsampling/tiling that TiTiler uses by default "behind the scenes").
- [x] Provide the user the option to reasonably format the result (e.g., `pandas`/`geopandas` or `rasterio DatasetReader`) to expedite use in general data science/GIS applications.
- [x] Make it easy to construct the proper syntax for retrieving the desired assets and/or expression (e.g., via both the whitelist and blacklist approach) for masking out undesirable classes. The user should have as close to the same parameters as are made available via the [titiler stac](https://developmentseed.org/titiler/endpoints/stac/) endpoints.
- [x] Support for passing a GeoJSON-like `dict` (i.e., contains a "type" member describing the type of the geometry and a "coordinates" member providing a list of coordinates).
- [x] Support for retrieving all data for a single geometry and a single date range.

## Outside scope (include in your application code)
- [ ] Support for passing a `shapely geometry`. Please use `geo_utils.vector.shapely_to_geojson_geometry()` to convert from `shapely geometry` to GeoJSON-like `dict` prior to calling `pixels_utils` code.
- [ ] Support for retrieving all data for multiple geometries and a single date range. Please use your application code to make calls across multiple geometries.
- [ ] Support for retrieving all data for multiple geometries and multiple date ranges (i.e., date ranges specific to each geometry). Please use your application code to make calls across multiple geometries, as well as to specify custom date ranges for each geometry.
PIXELS_URL = "https://pixels.sentera.com/stac/{endpoint}"

ENDPOINT_CROP = "crop"
ENDPOINT_INFO = "info"
ENDPOINT_STATISTICS = "statistics"

NODATA_STR = "nodata_value"


QUERY_URL = "url"  # STAC Item URL. Required
QUERY_ASSETS = "assets"  # asset names. Default to all available assets.
QUERY_EXPRESSION = (
    "expression"  # rio-tiler's math expression with asset names (e.g Asset1/Asset2).
)
QUERY_ASSET_BIDX = "asset_bidx"  # Per asset band math expression (e.g Asset1|1;2;3).
QUERY_ASSET_EXPRESSION = (
    "asset_expression"  # Per asset band math expression (e.g Asset1|b1\*b2).
)
QUERY_MAX_SIZE = "max_size"  # Max image size from which to calculate statistics, default is 1024. Ignored if height and width are provided.
QUERY_HEIGHT = "height"  # Force image height from which to calculate statistics.
QUERY_WIDTH = "width"  # Force image width from which to calculate statistics.
QUERY_NODATA = "nodata"  # Overwrite internal Nodata value.
QUERY_UNSCALE = "unscale"  # Apply dataset internal Scale/Offset.
QUERY_RESAMPLING = "resampling"  # rasterio resampling method. Default is nearest.
QUERY_CATEGORICAL = (
    "categorical"  # Return statistics for categorical dataset, default is false.
)
QUERY_C = "c"  # Pixels values for categories.
QUERY_P = "p"  # Percentile values.
QUERY_HISTOGRAM_BINS = "histogram_bins"  # Histogram bins.
QUERY_RANGE = "histogram_range"  # Comma (',') delimited Min,Max histogram bounds

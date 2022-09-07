import importlib


def requires_rasterio(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        rasterio_spec = importlib.util.find_spec("rasterio")
        found = rasterio_spec is not None
        if not found:
            raise ImportError("Missing optional dependency `rasterio`.")
        else:
            return func(*args, **kwargs)

    return wrapper

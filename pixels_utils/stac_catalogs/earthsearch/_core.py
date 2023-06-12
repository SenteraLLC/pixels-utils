from enum import Enum


class AutoDashNameEnum(Enum):
    """Sets the name of the enum to be the same as the value, but with underscores replaced with dashes."""

    def __init__(self, value):
        self._name_ = self._name_.replace("_", "-")
        self._value_ = value


# The EARTHSEARCH_ASSET_INFO_KEY dict maps the STAC version to the asset metadata/info key found in the collection
EARTHSEARCH_ASSET_INFO_KEY = {"1.0.0-beta.2": "info", "1.0.0": "tileinfo_metadata"}

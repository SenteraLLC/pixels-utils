from enum import Enum


class AutoDashNameEnum(Enum):
    """Sets the name of the enum to be the same as the value, but with underscores replaced with dashes."""

    def __init__(self, value):
        self._name_ = self._name_.replace("_", "-")
        self._value_ = value
